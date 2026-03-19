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
DEFAULT_SIMILARITY_THRESHOLD = 0.92  # Lowered from 0.95 to improve cache hit rate
DEFAULT_TTL_SECONDS = 14400  # 4 hours (answers don't change often)
DEFAULT_MAX_ENTRIES = 500


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

    _REDIS_KEY_PREFIX = "amt:cache:"
    _REDIS_INDEX_KEY = "amt:cache:index"  # sorted set of entry keys ordered by created_at

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        redis_url: str | None = None,
    ):
        self._entries: list[CacheEntry] = []
        self._lock = threading.Lock()
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
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
        return f"{self._REDIS_KEY_PREFIX}{h}"

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
            keys = self._redis.zrange(self._REDIS_INDEX_KEY, 0, -1)
            loaded = 0
            for key in keys:
                raw = self._redis.get(key)
                if raw is None:
                    # TTL expired in Redis but index wasn't cleaned up
                    self._redis.zrem(self._REDIS_INDEX_KEY, key)
                    continue
                entry = self._deserialize_entry(raw)
                if entry is None:
                    continue
                # Skip entries past their TTL
                if (now - entry.created_at) >= self.ttl_seconds:
                    continue
                self._entries.append(entry)
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
            self._redis.zadd(self._REDIS_INDEX_KEY, {key: entry.created_at})
            # Expire the index key to avoid unbounded growth
            self._redis.expire(self._REDIS_INDEX_KEY, self.ttl_seconds + 3600)
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
            self._entries = [
                e for e in self._entries if (now - e.created_at) < self.ttl_seconds
            ]

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

    def put(self, question: str, embedding: list[float], response: dict) -> None:
        """Store an answer in the cache."""
        with self._lock:
            # Don't cache error responses
            if not response.get("answer"):
                return

            # Evict oldest if at capacity
            if len(self._entries) >= self.max_entries:
                # Remove least recently created entries
                self._entries.sort(key=lambda e: e.created_at)
                self._entries = self._entries[-(self.max_entries // 2) :]

            entry = CacheEntry(
                question=question,
                embedding=embedding,
                response=response,
            )
            self._entries.append(entry)
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
            }

    def clear(self) -> None:
        """Clear all cache entries (in-memory and Redis)."""
        with self._lock:
            self._entries.clear()
            logger.info("Cache CLEARED")
        if self._redis:
            try:
                keys = self._redis.zrange(self._REDIS_INDEX_KEY, 0, -1)
                if keys:
                    self._redis.delete(*keys)
                self._redis.delete(self._REDIS_INDEX_KEY)
                logger.info("Redis cache CLEARED")
            except Exception as exc:
                logger.warning("Failed to clear Redis cache: %s", exc)


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
        )
    return _answer_cache
