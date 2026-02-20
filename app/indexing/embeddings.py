import hashlib
import math
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Singleton for caching the embedding model
_embedding_model = None
_openai_client = None


def _get_embedding_model():
    """Lazy load and cache the sentence-transformers model."""
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


def _get_openai_client():
    """Lazy load and cache the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        import os
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, 'openai_api_key', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set — required for openai embedding provider")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def embed_text(text: str) -> list[float]:
    if settings.embedding_provider == "openai":
        return _openai_embed([text], settings.embedding_dim)[0]

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

    if settings.embedding_provider == "openai":
        return _openai_embed(texts, settings.embedding_dim)

    if settings.embedding_provider == "sentence_transformers":
        model = _get_embedding_model()
        vecs = model.encode(texts)
        return [vec.tolist() for vec in vecs]

    # Local deterministic fallback
    return [_hashed_embedding(text, settings.embedding_dim) for text in texts]


def _openai_embed(texts: list[str], dim: int) -> list[list[float]]:
    """
    Embed texts using OpenAI text-embedding-3-small.
    
    Supports the `dimensions` parameter so we can request exactly 384 dims
    to match our existing DB column — no migration needed.
    """
    client = _get_openai_client()
    
    # OpenAI has a limit of ~8191 tokens per text and 2048 texts per batch
    # Process in batches of 500 to be safe
    BATCH_SIZE = 500
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        # Clean empty texts (OpenAI rejects them)
        batch = [t if t.strip() else "empty" for t in batch]
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
            dimensions=dim  # Request exactly 384 dims to match DB
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        
        if len(texts) > BATCH_SIZE:
            logger.info(f"OpenAI embeddings: batch {i // BATCH_SIZE + 1}/{(len(texts) + BATCH_SIZE - 1) // BATCH_SIZE} done")
    
    return all_embeddings


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
