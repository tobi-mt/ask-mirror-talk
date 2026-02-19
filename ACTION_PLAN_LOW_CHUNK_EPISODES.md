# Action Plan: Handling Large Episodes and Low-Chunk Episodes

## Current Situation

### ✅ What's Working
- **471 episodes** successfully ingested (100% coverage)
- **Average 93.7 chunks** per episode
- **345 episodes** with 50+ chunks (good coverage)
- MMR diversity algorithm working (88.9% unique episodes)

### ⚠️ Issues Identified

#### 1. **30 Episodes with Only 1-4 Chunks**
These episodes likely have:
- Very short duration (trailers, announcements)
- Poor audio quality (transcription failed)
- Large file size (partially processed then failed)

**Examples:**
- "Mark Robinson: Black On Madison Avenue" (1 chunk)
- "Born This Way" (1 chunk)
- "Creating Your Reality with Jay Campbell" (1 chunk)

#### 2. **Large Audio Files (>25MB) Are Skipped in Production**
Based on code analysis:
- Production setting: `ENABLE_AUDIO_COMPRESSION=false` (assumed)
- Files >25MB are rejected during download
- No compression happens before transcription

## Root Cause Analysis

### Why Compression is Disabled in Production

Looking at the codebase history:
```dockerfile
# Dockerfile.worker line 3:
# Force rebuild - updated 2026-02-15 00:00 UTC (DISABLE compression to prevent OOM)
```

**Reason:** Memory constraints on Railway
- FFmpeg compression uses significant memory
- Worker service has limited RAM (512MB-1GB)
- OOM (Out of Memory) crashes occurred during compression

### The Tradeoff
| Enable Compression | Disable Compression |
|-------------------|---------------------|
| ✅ Process large episodes (25-40MB) | ✅ No OOM crashes |
| ✅ Better episode coverage | ✅ Lower memory usage |
| ✅ More diverse citations | ✅ Faster ingestion |
| ❌ Risk of OOM crashes | ❌ Skip large episodes |
| ❌ Higher memory usage | ❌ Gaps in coverage |

## Recommended Solutions

### Solution 1: Selective Re-ingestion (Local) ✨ RECOMMENDED

**Process only the low-chunk episodes locally with compression enabled**

#### Step 1: Identify Episodes to Re-ingest
```python
# From analyze_episode_engagement.py output:
# 30 episodes with 1-4 chunks
# 7 episodes with 5-9 chunks
```

#### Step 2: Create Re-ingestion Script
```bash
# scripts/reingest_low_chunk_episodes.py
```

This script will:
1. Query database for episodes with <5 chunks
2. Extract their RSS GUIDs
3. Re-ingest using local environment (no size limit, compression enabled)
4. Upload new chunks to production database

#### Step 3: Run Local Re-ingestion
```bash
# Enable compression locally
export ENABLE_AUDIO_COMPRESSION=true
export MAX_AUDIO_SIZE_MB=0  # No limit

# Run re-ingestion
python scripts/reingest_low_chunk_episodes.py
```

**Benefits:**
- ✅ No production changes needed
- ✅ No OOM risk (runs locally)
- ✅ Improves coverage for problematic episodes
- ✅ One-time backfill operation

**Tradeoffs:**
- ⏱️ Requires local execution
- 💻 Needs local resources (FFmpeg, OpenAI API)
- 🔄 Manual process (not automated)

---

### Solution 2: Enable Compression in Production (Advanced)

**Enable compression on Railway worker with memory optimization**

#### Changes Required:

1. **Add Environment Variable:**
```bash
# In Railway Dashboard → Worker Service → Variables
ENABLE_AUDIO_COMPRESSION=true
```

2. **Increase Worker Memory:**
```bash
# In Railway Dashboard → Worker Service → Settings
# Increase memory allocation to 2GB (currently 512MB-1GB)
```

3. **Add Memory Monitoring:**
```python
# In app/ingestion/pipeline_optimized.py
# Log memory usage before/after compression
```

**Benefits:**
- ✅ Automatic handling of large episodes
- ✅ No manual intervention needed
- ✅ Future episodes handled automatically

**Tradeoffs:**
- 💰 Higher Railway costs (more memory)
- ⚠️ Risk of OOM if memory insufficient
- 🐛 Requires testing and monitoring

**Cost Impact:**
- Current: ~$5-10/month (512MB worker)
- With 2GB: ~$20-30/month
- Additional cost: ~$10-20/month

---

### Solution 3: Hybrid Approach (Balanced)

**Combine local re-ingestion with smart production limits**

#### Part A: Local Re-ingestion (One-time)
- Re-ingest 30 low-chunk episodes locally
- Improve coverage for existing content

#### Part B: Production Optimization (Ongoing)
- Keep compression disabled (avoid OOM)
- Set smarter size limits:
  ```bash
  MAX_AUDIO_SIZE_MB=30  # Allow slightly larger files
  ```
- Add better error handling and retries
- Monitor skipped episodes and flag for manual processing

**Benefits:**
- ✅ Best of both worlds
- ✅ Immediate improvement (local re-ingestion)
- ✅ Low risk (no production memory issues)
- ✅ Sustainable long-term

---

## Detailed Implementation: Solution 1 (Recommended)

### Script: `scripts/reingest_low_chunk_episodes.py`

```python
"""
Re-ingest episodes that have very few chunks.
This script identifies episodes with <5 chunks and re-processes them
with compression enabled to improve coverage.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from app.core.db import get_session_local
from app.storage import models
from app.ingestion.pipeline_optimized import run_ingestion_optimized

def get_low_chunk_episodes(db, max_chunks: int = 4):
    """Get episodes with fewer than max_chunks chunks."""
    # Query episodes with chunk count
    results = (
        db.query(models.Episode, func.count(models.Chunk.id).label('chunk_count'))
        .outerjoin(models.Chunk)
        .group_by(models.Episode.id)
        .having(func.count(models.Chunk.id) <= max_chunks)
        .order_by(func.count(models.Chunk.id))
        .all()
    )
    
    return [(episode, chunk_count) for episode, chunk_count in results]

def main():
    # Check environment
    compression_enabled = os.getenv('ENABLE_AUDIO_COMPRESSION', 'true').lower() == 'true'
    max_size = os.getenv('MAX_AUDIO_SIZE_MB', '25')
    
    print("🔍 Re-ingestion Configuration:")
    print(f"  ENABLE_AUDIO_COMPRESSION: {compression_enabled}")
    print(f"  MAX_AUDIO_SIZE_MB: {max_size}")
    print()
    
    if not compression_enabled:
        print("⚠️  WARNING: Compression is disabled!")
        print("   Run: export ENABLE_AUDIO_COMPRESSION=true")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    SessionMaker = get_session_local()
    db = SessionMaker()
    
    try:
        # Get episodes with <5 chunks
        low_chunk_episodes = get_low_chunk_episodes(db, max_chunks=4)
        
        print(f"📊 Found {len(low_chunk_episodes)} episodes with ≤4 chunks\n")
        
        if not low_chunk_episodes:
            print("✅ No episodes need re-ingestion!")
            return
        
        # Show episodes
        print("Episodes to re-ingest:")
        print("-" * 80)
        for episode, chunk_count in low_chunk_episodes[:10]:
            title = episode.title[:60] + "..." if len(episode.title) > 60 else episode.title
            print(f"  {episode.episode_number}. {title} ({chunk_count} chunks)")
        
        if len(low_chunk_episodes) > 10:
            print(f"  ... and {len(low_chunk_episodes) - 10} more")
        print()
        
        # Confirm
        response = input(f"Re-ingest {len(low_chunk_episodes)} episodes? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Convert to entry format for pipeline
        entries = []
        for episode, _ in low_chunk_episodes:
            entries.append({
                'guid': episode.guid,
                'title': episode.title,
                'audio_url': episode.audio_url,
                'description': episode.description,
                'published_at': episode.published_at,
                'episode_number': episode.episode_number,
                'duration': episode.duration,
            })
        
        # Run ingestion with these specific entries
        print(f"\n🚀 Starting re-ingestion of {len(entries)} episodes...\n")
        
        result = run_ingestion_optimized(
            db,
            max_episodes=len(entries),
            entries_to_process=entries
        )
        
        print(f"\n✅ Re-ingestion complete!")
        print(f"  Processed: {result['processed']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Failed: {result['failed']}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

### Usage Instructions:

#### 1. Set Up Local Environment
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Enable compression
export ENABLE_AUDIO_COMPRESSION=true

# Remove size limit
export MAX_AUDIO_SIZE_MB=0

# Ensure FFmpeg is installed
brew install ffmpeg  # macOS

# Ensure OpenAI API key is set
export OPENAI_API_KEY="your-key"

# Ensure database connection
export DATABASE_URL="your-production-db-url"
```

#### 2. Run Re-ingestion
```bash
python scripts/reingest_low_chunk_episodes.py
```

#### 3. Verify Results
```bash
# Check improved chunk counts
python scripts/analyze_episode_engagement.py
```

#### 4. Monitor Progress
- Episodes with 1 chunk should now have 50-200+ chunks
- Total coverage should improve
- Citations should include previously skipped episodes

---

## Expected Outcomes

### Before Re-ingestion:
- 30 episodes with 1-4 chunks
- Average: 93.7 chunks/episode
- Some large episodes skipped

### After Re-ingestion:
- 0-5 episodes with 1-4 chunks (only true shorts/trailers)
- Average: 95-100 chunks/episode
- All processable episodes included
- Better citation diversity

---

## Monitoring Plan

### 1. Run Engagement Analysis Weekly
```bash
python scripts/analyze_episode_engagement.py > reports/engagement_$(date +%Y%m%d).txt
```

### 2. Check for New Low-Chunk Episodes
```bash
# After each ingestion run:
grep "chunks)" reports/engagement_latest.txt | grep "1 chunks"
```

### 3. Monitor Skipped Episodes
```bash
# Check logs for size-related skips:
grep "Audio file too large" logs/*.log
```

---

## Decision Matrix

| Scenario | Recommended Solution |
|----------|---------------------|
| **One-time improvement needed** | Solution 1 (Local re-ingestion) |
| **Ongoing large episodes expected** | Solution 2 (Enable production compression) |
| **Budget-conscious** | Solution 3 (Hybrid approach) |
| **Production stability critical** | Solution 1 (Local only) |

---

## Next Steps

### Immediate (Today):
1. ✅ Review this action plan
2. ⬜ Create `scripts/reingest_low_chunk_episodes.py`
3. ⬜ Test on 1-2 episodes locally
4. ⬜ Run full re-ingestion for low-chunk episodes

### Short-term (This Week):
5. ⬜ Analyze results and verify improvements
6. ⬜ Update monitoring scripts to flag new low-chunk episodes
7. ⬜ Document process for future re-ingestions

### Long-term (Optional):
8. ⬜ Consider enabling compression in production (if budget allows)
9. ⬜ Set up automated monitoring for episode coverage
10. ⬜ Add alerting for consistently skipped episodes

---

## Questions & Answers

### Q: Why not just enable compression in production?
**A:** Memory constraints. Railway worker has limited RAM and compression caused OOM crashes. Local processing avoids this risk.

### Q: Will this improve search results?
**A:** Yes! Episodes with only 1 chunk have limited text coverage. Re-ingestion will create 50-200+ chunks per episode, significantly improving search quality.

### Q: How long will re-ingestion take?
**A:** ~30-60 seconds per episode (download + compress + transcribe + chunk). For 30 episodes: ~15-30 minutes total.

### Q: What if some episodes still fail?
**A:** Episodes that are truly too short (trailers, announcements) will naturally have 1-4 chunks. That's expected and okay.

### Q: Can this be automated?
**A:** Yes, but would require:
- Scheduled local job (cron)
- Secure database access
- API key management
- Error handling and monitoring

For now, manual execution is simpler and safer.

---

## Conclusion

**Recommended Action:** Implement Solution 1 (Local Re-ingestion)

This provides immediate improvement without production risks or cost increases. You can always consider production compression later if needed.

**Success Criteria:**
- ✅ Low-chunk episodes reduced from 30 to <10
- ✅ Average chunks/episode increased to 95+
- ✅ No new production errors or crashes
- ✅ Better citation diversity in search results
