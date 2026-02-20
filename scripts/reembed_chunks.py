#!/usr/bin/env python3
"""
Re-embed all chunks using OpenAI text-embedding-3-small.

This script updates the embedding vectors for ALL existing chunks in the database
WITHOUT re-downloading audio, re-transcribing, or re-chunking. It only touches
the `embedding` column.

Why: The original hash-based embeddings (EMBEDDING_PROVIDER=local) are bag-of-words
and cannot do semantic search. OpenAI embeddings understand meaning, so a query
about "addiction" will find episodes about recovery, substance abuse, compulsion, etc.

Usage:
    # Set environment variables first
    export EMBEDDING_PROVIDER=openai
    export OPENAI_API_KEY=sk-...
    export DATABASE_URL=postgresql+psycopg://...

    # Run (takes ~5-10 minutes for 44,885 chunks)
    python scripts/reembed_chunks.py

    # Or with a batch size override
    python scripts/reembed_chunks.py --batch-size 200

Cost estimate:
    - 44,885 chunks × ~100 tokens avg = ~4.5M tokens
    - text-embedding-3-small: $0.02/1M tokens
    - Total cost: ~$0.09 (less than 10 cents!)
"""

import argparse
import logging
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.db import engine, SessionLocal
from app.storage.models import Chunk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def reembed_all_chunks(batch_size: int = 500, dry_run: bool = False):
    """
    Re-embed all chunks in the database using the current EMBEDDING_PROVIDER.
    
    Args:
        batch_size: Number of chunks to embed at once (500 is optimal for OpenAI)
        dry_run: If True, only count chunks without updating
    """
    from app.indexing.embeddings import embed_text_batch
    
    logger.info("=" * 60)
    logger.info("RE-EMBEDDING ALL CHUNKS")
    logger.info("=" * 60)
    logger.info(f"Embedding provider: {settings.embedding_provider}")
    logger.info(f"Embedding dimensions: {settings.embedding_dim}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Dry run: {dry_run}")
    
    if settings.embedding_provider == "local":
        logger.error("❌ EMBEDDING_PROVIDER is still 'local'!")
        logger.error("   Set EMBEDDING_PROVIDER=openai before running this script.")
        logger.error("   Example: export EMBEDDING_PROVIDER=openai")
        sys.exit(1)
    
    # SessionLocal is a function that returns a sessionmaker
    # Need to call it twice: once to get the factory, once to get a session
    db = SessionLocal()()
    
    try:
        # Count total chunks
        total_chunks = db.query(Chunk.id).count()
        logger.info(f"Total chunks in database: {total_chunks}")
        
        if dry_run:
            logger.info("🔍 Dry run complete. No changes made.")
            return
        
        if total_chunks == 0:
            logger.warning("No chunks found in database.")
            return
        
        # Process in batches
        start_time = time.time()
        processed = 0
        errors = 0
        
        # Fetch all chunk IDs to process in order
        all_ids = [row[0] for row in db.query(Chunk.id).order_by(Chunk.id).all()]
        
        for batch_start in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[batch_start:batch_start + batch_size]
            
            # Fetch chunks for this batch
            chunks = db.query(Chunk).filter(Chunk.id.in_(batch_ids)).order_by(Chunk.id).all()
            texts = [chunk.text for chunk in chunks]
            
            try:
                # Embed the batch
                embeddings = embed_text_batch(texts)
                
                # Update each chunk's embedding
                for chunk, embedding in zip(chunks, embeddings):
                    chunk.embedding = embedding
                
                # Commit this batch
                db.commit()
                processed += len(chunks)
                
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_chunks - processed) / rate if rate > 0 else 0
                
                logger.info(
                    f"✅ Batch {batch_start // batch_size + 1}: "
                    f"{processed}/{total_chunks} chunks "
                    f"({processed * 100 / total_chunks:.1f}%) "
                    f"| {rate:.0f} chunks/sec "
                    f"| ETA: {eta:.0f}s"
                )
                
            except Exception as e:
                db.rollback()
                errors += 1
                logger.error(f"❌ Batch error at chunk IDs {batch_ids[0]}-{batch_ids[-1]}: {e}")
                
                # Retry individual chunks in failed batch
                logger.info("   Retrying individual chunks...")
                for chunk in chunks:
                    try:
                        from app.indexing.embeddings import embed_text
                        chunk.embedding = embed_text(chunk.text)
                        db.commit()
                        processed += 1
                    except Exception as e2:
                        db.rollback()
                        logger.error(f"   ❌ Failed chunk {chunk.id}: {e2}")
                        errors += 1
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("RE-EMBEDDING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Processed: {processed}/{total_chunks} chunks")
        logger.info(f"❌ Errors: {errors}")
        logger.info(f"⏱️  Time: {elapsed:.1f}s ({elapsed / 60:.1f} min)")
        logger.info(f"📊 Rate: {processed / elapsed:.0f} chunks/sec")
        logger.info(f"🔧 Provider: {settings.embedding_provider}")
        
        if errors > 0:
            logger.warning(f"⚠️  {errors} chunks failed. You may want to re-run.")
        else:
            logger.info("🎉 All chunks successfully re-embedded!")
            logger.info("")
            logger.info("NEXT STEPS:")
            logger.info("1. Set EMBEDDING_PROVIDER=openai on Railway (Variables tab)")
            logger.info("2. Redeploy the API service")
            logger.info("3. Test: curl -X POST .../ask -d '{\"question\": \"addiction\"}'")
            logger.info("4. Verify addiction-related episodes now appear!")
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-embed all chunks with semantic embeddings")
    parser.add_argument("--batch-size", type=int, default=500, help="Chunks per batch (default: 500)")
    parser.add_argument("--dry-run", action="store_true", help="Count chunks without updating")
    args = parser.parse_args()
    
    reembed_all_chunks(batch_size=args.batch_size, dry_run=args.dry_run)
