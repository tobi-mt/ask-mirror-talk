"""
One-time migration: create HNSW vector index on chunks.embedding

Without this index every vector search is a full sequential scan over all
45K+ chunk embeddings, growing from ~100ms to 10+ seconds as the corpus
expands.  This script creates the index once on the existing production DB.

Usage (run from project root):
    python scripts/create_hnsw_index.py

The script is idempotent (CREATE INDEX IF NOT EXISTS) so it's safe to re-run.
Index creation on ~45K 384-dim vectors takes roughly 30–90 seconds.
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    from app.core.db import get_engine
    from sqlalchemy import text

    engine = get_engine()

    logger.info("Connecting to database…")
    with engine.connect() as conn:
        # Check current chunk count so user knows how long to expect
        row = conn.execute(text("SELECT COUNT(*) FROM chunks")).fetchone()
        chunk_count = row[0] if row else 0
        logger.info("Current chunk count: %d", chunk_count)

        # Check if index already exists
        exists = conn.execute(text(
            "SELECT 1 FROM pg_indexes "
            "WHERE tablename = 'chunks' AND indexname = 'chunks_embedding_hnsw'"
        )).fetchone()

        if exists:
            logger.info("HNSW index already exists — nothing to do.")
            return

        logger.info("Creating HNSW index (this may take 30–90 seconds for ~45K rows)…")
        start = time.time()

        # set_maintenance_work_mem helps pgvector build the index faster
        conn.execute(text("SET maintenance_work_mem = '256MB'"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw "
            "ON chunks USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        ))
        conn.commit()

        elapsed = time.time() - start
        logger.info("✓ HNSW index created in %.1f seconds", elapsed)

        # Verify
        row = conn.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE tablename = 'chunks' AND indexname = 'chunks_embedding_hnsw'"
        )).fetchone()
        if row:
            logger.info("Index verified: %s", row[0])
        else:
            logger.error("Index creation appeared to succeed but index not found!")
            sys.exit(1)


if __name__ == "__main__":
    main()
