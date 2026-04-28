"""
Answer Cache for Ask Mirror Talk

Caches answers for frequently asked or near-identical questions using
embedding similarity. Returns cached answers instantly when a match
is found above the similarity threshold.

Primary store: in-memory with a TTL (fast lookups, O(n) similarity scan).
Persistence layer: optional Redis (set REDIS_URL env var) — survives
restarts/deploys so the pre-warm dataset is not lost on every deploy.
"""

import time
import threading
import logging
import math
import json
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


def normalize_question(q: str) -> str:
    """
    Normalize a question for cache matching.
    Strips whitespace, lowercases, removes trailing punctuation.
    Ensures semantically identical questions hit the same cache entry.
    """
    import re
    q = q.strip().lower()
    # Remove trailing question marks and periods
    q = re.sub(r'[?.!]+$', '', q).strip()
    # Collapse multiple spaces
    q = re.sub(r'\s+', ' ', q)
    return q

# Default settings
DEFAULT_SIMILARITY_THRESHOLD = 0.88  # Lowered to 0.88 to catch more question variations (was 0.92)
DEFAULT_TTL_SECONDS = 14400  # 4 hours (answers don't change often)
DEFAULT_MAX_ENTRIES = 500


def _looks_like_degraded_answer_text(answer: str) -> bool:
    text = (answer or "").strip().lower()
    return text.startswith((
        "i found related mirror talk material, but i could not generate",
        "i found a few mirror talk moments",
        "here are grounded reflections",
        "the clearest thread is this:",
    ))


@dataclass
class CacheEntry:
    question: str
    embedding: list[float]
    response: dict
    created_at: float = field(default_factory=time.time)
    hit_count: int = 0


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class AnswerCache:
    """
    Thread-safe in-memory answer cache with embedding-based similarity lookup.

    When a Redis URL is configured, entries are also persisted to Redis so the
    cache survives application restarts and Railway deploys.  Redis is used as
    a write-through / read-on-startup persistence layer; all hot-path reads and
    similarity scans always happen in-memory for speed.
    """

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        redis_url: str | None = None,
        namespace: str = "default",
    ):
        self._entries: list[CacheEntry] = []
        self._entries_by_question: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.namespace = (namespace or "default").strip()
        self._redis = None

        if redis_url:
            self._connect_redis(redis_url)
            self._load_from_redis()

    # ── Redis helpers ──────────────────────────────────────────────────────

    def _connect_redis(self, redis_url: str) -> None:
        try:
            import redis as redis_lib
            self._redis = redis_lib.from_url(
                redis_url,
                decode_responses=False,  # we handle serialisation manually
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            self._redis.ping()
            logger.info("Redis cache backend connected: %s", redis_url.split("@")[-1])
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — falling back to in-memory only", exc)
            self._redis = None

    def _entry_redis_key(self, question: str) -> str:
        import hashlib
        h = hashlib.sha256(question.encode()).hexdigest()[:16]
        return f"amt:cache:{self.namespace}:{h}"

    @property
    def _redis_index_key(self) -> str:
        return f"amt:cache:index:{self.namespace}"

    def _serialize_entry(self, entry: CacheEntry) -> bytes:
        """Serialise a CacheEntry to JSON bytes (no pickle for safety)."""
        data = {
            "question": entry.question,
            "embedding": entry.embedding,
            "response": entry.response,
            "created_at": entry.created_at,
            "hit_count": entry.hit_count,
        }
        return json.dumps(data).encode()

    def _deserialize_entry(self, raw: bytes) -> CacheEntry | None:
        try:
            data = json.loads(raw.decode())
            return CacheEntry(
                question=data["question"],
                embedding=data["embedding"],
                response=data["response"],
                created_at=data["created_at"],
                hit_count=data.get("hit_count", 0),
            )
        except Exception as exc:
            logger.warning("Failed to deserialise Redis cache entry: %s", exc)
            return None

    def _load_from_redis(self) -> None:
        """Populate in-memory cache from Redis on startup."""
        if not self._redis:
            return
        try:
            now = time.time()
            # Fetch all entry keys from the sorted set (score = created_at)
            keys = self._redis.zrange(self._redis_index_key, 0, -1)
            loaded = 0
            for key in keys:
                raw = self._redis.get(key)
                if raw is None:
                    # TTL expired in Redis but index wasn't cleaned up
                    self._redis.zrem(self._redis_index_key, key)
                    continue
                entry = self._deserialize_entry(raw)
                if entry is None:
                    continue
                # Skip entries past their TTL
                if (now - entry.created_at) >= self.ttl_seconds:
                    continue
                self._entries.append(entry)
                self._entries_by_question[entry.question] = entry
                loaded += 1
            logger.info("Loaded %d entries from Redis cache", loaded)
        except Exception as exc:
            logger.warning("Failed to load cache from Redis: %s", exc)

    def _persist_to_redis(self, entry: CacheEntry) -> None:
        """Write a single entry to Redis (write-through)."""
        if not self._redis:
            return
        try:
            key = self._entry_redis_key(entry.question)
            raw = self._serialize_entry(entry)
            remaining_ttl = max(1, int(self.ttl_seconds - (time.time() - entry.created_at)))
            self._redis.setex(key, remaining_ttl, raw)
            # Track in sorted set so we can efficiently load all entries later
            self._redis.zadd(self._redis_index_key, {key: entry.created_at})
            # Expire the index key to avoid unbounded growth
            self._redis.expire(self._redis_index_key, self.ttl_seconds + 3600)
        except Exception as exc:
            logger.warning("Failed to persist cache entry to Redis: %s", exc)

    def get(self, question: str, embedding: list[float]) -> dict | None:
        """
        Look up a cached answer by embedding similarity.

        Returns the cached response dict if a match is found, otherwise None.
        """
        now = time.time()

        with self._lock:
            # Evict expired entries
            fresh_entries = [
                e for e in self._entries if (now - e.created_at) < self.ttl_seconds
            ]
            if len(fresh_entries) != len(self._entries):
                self._entries = fresh_entries
                self._entries_by_question = {e.question: e for e in self._entries}

            best_match: CacheEntry | None = None
            best_similarity = 0.0

            for entry in self._entries:
                sim = _cosine_similarity(embedding, entry.embedding)
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = entry

            if best_match and best_similarity >= self.similarity_threshold:
                best_match.hit_count += 1
                logger.info(
                    "Cache HIT: '%.60s' matched '%.60s' (similarity=%.4f, hits=%d)",
                    question,
                    best_match.question,
                    best_similarity,
                    best_match.hit_count,
                )
                # Return a copy with cache metadata
                cached = dict(best_match.response)
                cached["cached"] = True
                cached["cache_similarity"] = round(best_similarity, 4)
                return cached

            logger.debug(
                "Cache MISS: '%.60s' (best_similarity=%.4f)",
                question,
                best_similarity,
            )
            return None

    def get_exact(self, question: str) -> dict | None:
        """Look up a cached answer by exact normalized question match."""
        now = time.time()

        with self._lock:
            entry = self._entries_by_question.get(question)
            if not entry:
                return None
            if (now - entry.created_at) >= self.ttl_seconds:
                self._entries = [e for e in self._entries if e.question != question]
                self._entries_by_question.pop(question, None)
                return None

            entry.hit_count += 1
            logger.info(
                "Cache EXACT HIT: '%.60s' (hits=%d)",
                question,
                entry.hit_count,
            )
            cached = dict(entry.response)
            cached["cached"] = True
            cached["cache_similarity"] = 1.0
            cached["cache_match_type"] = "exact"
            return cached

    def put(self, question: str, embedding: list[float], response: dict) -> None:
        """Store an answer in the cache."""
        with self._lock:
            # Don't cache error responses
            if not response.get("answer"):
                return
            if (
                response.get("answer_source") in {"basic_fallback", "no_match"}
                or response.get("answer_status") in {"generation_failed", "source_moments_only", "needs_refinement"}
                or _looks_like_degraded_answer_text(str(response.get("answer") or ""))
            ):
                logger.info("Cache SKIP: degraded answer for '%.60s'", question)
                return

            # Evict oldest if at capacity
            if len(self._entries) >= self.max_entries:
                # Remove least recently created entries
                self._entries.sort(key=lambda e: e.created_at)
                self._entries = self._entries[-(self.max_entries // 2) :]
                self._entries_by_question = {e.question: e for e in self._entries}

            entry = CacheEntry(
                question=question,
                embedding=embedding,
                response=response,
            )
            self._entries.append(entry)
            self._entries_by_question[entry.question] = entry
            logger.info("Cache PUT: '%.60s' (total entries: %d)", question, len(self._entries))

        # Persist outside the lock to avoid blocking cache reads
        self._persist_to_redis(entry)

    def stats(self) -> dict:
        """Return cache statistics."""
        with self._lock:
            total_hits = sum(e.hit_count for e in self._entries)
            return {
                "entries": len(self._entries),
                "max_entries": self.max_entries,
                "total_hits": total_hits,
                "ttl_seconds": self.ttl_seconds,
                "similarity_threshold": self.similarity_threshold,
                "namespace": self.namespace,
            }

    def clear(self) -> None:
        """Clear all cache entries (in-memory and Redis)."""
        with self._lock:
                self._entries.clear()
                self._entries_by_question.clear()
                logger.info("Cache CLEARED")
        if self._redis:
            try:
                keys = self._redis.zrange(self._redis_index_key, 0, -1)
                if keys:
                    self._redis.delete(*keys)
                self._redis.delete(self._redis_index_key)
                logger.info("Redis cache CLEARED")
            except Exception as exc:
                logger.warning("Failed to clear Redis cache: %s", exc)


def prewarm_from_db_history(cache: "AnswerCache", db, limit: int = 40) -> int:
    """
    Load the most-asked historical user questions into the cache without
    making any OpenAI calls.  Re-embeds each question locally (fast), then
    stores the saved answer + reconstructed citation list from qa_logs so
    those answers survive app restarts instantly.

    Returns the number of entries successfully loaded.
    """
    from sqlalchemy import text as sqla_text
    from app.indexing.embeddings import embed_text

    try:
        # Pick the single most-recent answer for the top N most-asked questions.
        # Skip rows that had no answer (is_answered = FALSE) and empty episode_ids.
        rows = db.execute(sqla_text("""
            SELECT q.question, q.answer, q.episode_ids
            FROM qa_logs q
            INNER JOIN (
                SELECT question,
                       COUNT(*)  AS cnt,
                       MAX(id)   AS latest_id
                FROM qa_logs
                WHERE (is_answered = TRUE OR is_answered IS NULL)
                  AND episode_ids IS NOT NULL
                  AND episode_ids != ''
                GROUP BY question
                ORDER BY cnt DESC
                LIMIT :lim
            ) freq ON q.id = freq.latest_id
            ORDER BY freq.cnt DESC
        """), {"lim": limit}).fetchall()
    except Exception as exc:
        logger.warning("Cache DB prewarm: failed to query qa_logs — %s", exc)
        return 0

    if not rows:
        return 0

    # Bulk-fetch the best representative chunk per episode.
    # Pick the chunk with the longest text (most substantive) per episode,
    # joined with episode metadata for the title/audio_url.
    # Intro chunks tend to be short, so "longest text" naturally avoids them.
    all_ep_ids: set[int] = set()
    for _, _, ep_ids_str in rows:
        for raw in (ep_ids_str or "").split(","):
            raw = raw.strip()
            if raw.isdigit():
                all_ep_ids.add(int(raw))

    ep_map: dict[int, dict] = {}
    if all_ep_ids:
        try:
            ep_rows = db.execute(sqla_text("""
                SELECT DISTINCT ON (c.episode_id)
                    e.id,
                    e.title,
                    e.audio_url,
                    EXTRACT(YEAR FROM e.published_at)::int AS yr,
                    c.text,
                    c.start_time,
                    c.end_time
                FROM chunks c
                JOIN episodes e ON c.episode_id = e.id
                WHERE e.id = ANY(:ids)
                  AND c.text IS NOT NULL
                  AND length(c.text) > 50
                ORDER BY c.episode_id, length(c.text) DESC
            """), {"ids": list(all_ep_ids)}).fetchall()
            ep_map = {
                r[0]: {
                    "title": r[1] or "",
                    "audio_url": r[2] or "",
                    "year": int(r[3]) if r[3] else None,
                    "text": r[4] or "",
                    "start_time": float(r[5]) if r[5] is not None else 0.0,
                    "end_time": float(r[6]) if r[6] is not None else 0.0,
                }
                for r in ep_rows
            }
        except Exception as exc:
            logger.warning("Cache DB prewarm: failed to fetch episode chunks — %s", exc)

    loaded = 0
    for question, answer, ep_ids_str in rows:
        try:
            if _looks_like_degraded_answer_text(str(answer or "")):
                logger.info("Cache DB prewarm: skipped degraded historical answer for '%.50s'", question)
                continue
            ep_ids = [
                int(x.strip()) for x in (ep_ids_str or "").split(",")
                if x.strip().isdigit()
            ]
            citations = [
                {
                    "episode_id": eid,
                    "episode_title": ep_map[eid]["title"],
                    "episode_year": ep_map[eid]["year"],
                    "audio_url": ep_map[eid]["audio_url"],
                    "episode_url": (
                        f"{ep_map[eid]['audio_url']}#t={int(ep_map[eid]['start_time'])}"
                        if ep_map[eid]["audio_url"] and ep_map[eid]["start_time"] > 0
                        else ep_map[eid]["audio_url"]
                    ),
                    "timestamp_start_seconds": int(ep_map[eid]["start_time"]),
                    "timestamp_end_seconds": int(ep_map[eid]["end_time"]),
                    "text": ep_map[eid]["text"][:200],
                }
                for eid in ep_ids
                if eid in ep_map
            ]
            norm_q = normalize_question(question)
            embedding = embed_text(norm_q)
            cache.put(norm_q, embedding, {
                "question": question,
                "answer": answer,
                "citations": citations,
                "follow_up_questions": [],
            })
            loaded += 1
        except Exception as exc:
            logger.warning("Cache DB prewarm: failed for '%.50s' — %s", question, exc)

    logger.info("Cache DB prewarm: loaded %d / %d historical entries", loaded, len(rows))
    return loaded


# Global singleton
_answer_cache: AnswerCache | None = None


def get_answer_cache() -> AnswerCache:
    """Get the global answer cache singleton, using config from settings."""
    global _answer_cache
    if _answer_cache is None:
        from app.core.config import settings
        _answer_cache = AnswerCache(
            similarity_threshold=settings.cache_similarity_threshold,
            ttl_seconds=settings.cache_ttl_seconds,
            redis_url=settings.redis_url,
            namespace=settings.cache_namespace,
        )
    return _answer_cache
