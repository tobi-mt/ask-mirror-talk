import hashlib
import math
from app.core.config import settings


# Singleton for caching the embedding model
_embedding_model = None


def _get_embedding_model():
    """Lazy load and cache the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers not installed. Install optional dependency 'embeddings'."
            ) from exc
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def embed_text(text: str) -> list[float]:
    if settings.embedding_provider == "sentence_transformers":
        model = _get_embedding_model()
        vec = model.encode([text])[0]
        return vec.tolist()

    # Local deterministic fallback: hashed bag-of-words embedding
    return _hashed_embedding(text, settings.embedding_dim)


def embed_text_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts at once for better performance."""
    if not texts:
        return []
    
    if settings.embedding_provider == "sentence_transformers":
        model = _get_embedding_model()
        # Batch encoding is much faster than encoding one at a time
        vecs = model.encode(texts)
        return [vec.tolist() for vec in vecs]
    
    # Local deterministic fallback
    return [_hashed_embedding(text, settings.embedding_dim) for text in texts]


def _hashed_embedding(text: str, dim: int) -> list[float]:
    tokens = [t for t in text.lower().split() if t.isalpha()]
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    for token in tokens:
        h = hashlib.sha256(token.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % dim
        vec[idx] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]
