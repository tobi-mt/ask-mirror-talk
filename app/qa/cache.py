"""
Answer Cache for Ask Mirror Talk

Caches answers for frequently asked or near-identical questions using
embedding similarity. Returns cached answers instantly when a match
is found above the similarity threshold.

Cache is stored in-memory with a TTL. For production at scale,
this could be backed by Redis.
"""

import time
import threading
import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SIMILARITY_THRESHOLD = 0.95
DEFAULT_TTL_SECONDS = 3600  # 1 hour
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
    """

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        self._entries: list[CacheEntry] = []
        self._lock = threading.Lock()
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries

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

            self._entries.append(
                CacheEntry(
                    question=question,
                    embedding=embedding,
                    response=response,
                )
            )
            logger.info("Cache PUT: '%.60s' (total entries: %d)", question, len(self._entries))

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
        """Clear all cache entries."""
        with self._lock:
            self._entries.clear()
            logger.info("Cache CLEARED")


# Global singleton
_answer_cache: AnswerCache | None = None


def get_answer_cache() -> AnswerCache:
    """Get the global answer cache singleton."""
    global _answer_cache
    if _answer_cache is None:
        _answer_cache = AnswerCache()
    return _answer_cache
