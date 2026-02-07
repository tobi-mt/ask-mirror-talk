import hashlib
import math
from app.core.config import settings


def embed_text(text: str) -> list[float]:
    if settings.embedding_provider == "sentence_transformers":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers not installed. Install optional dependency 'embeddings'."
            ) from exc
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = model.encode([text])[0]
        return vec.tolist()

    # Local deterministic fallback: hashed bag-of-words embedding
    return _hashed_embedding(text, settings.embedding_dim)


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
