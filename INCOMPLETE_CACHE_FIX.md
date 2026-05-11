# Fix for Incomplete Cached Answers

## Problem

The cache was storing and serving incomplete answers that were cut off mid-sentence. This happened when:

1. A streaming answer generation starts
2. The OpenAI API stream gets interrupted or times out before completing
3. The partial text accumulated in `full_answer` still gets cached
4. Future requests hit this cache and return the incomplete answer

### Example

The question "What does rest really look like in a culture of hustle?" had a cached answer ending with:
```
"...it's clear that true rest isn"
```

The answer was incomplete (cut off mid-sentence), but was still cached and served to users with 2 cache hits.

## Root Cause

The code in `answer_question_stream()` and `answer_question()` cached answers without validating if they were complete:

```python
# Old code - no validation
if _is_degraded_cached_answer(cache_payload):
    logger.info("Skipping cache PUT for degraded streaming answer to '%.80s'", question)
else:
    cache.put(norm_q, query_embedding, cache_payload)  # ❌ Caches incomplete answers
```

## Solution

### 1. Added Incomplete Answer Detection

Created `_is_incomplete_answer()` function in [app/qa/service.py](app/qa/service.py) that checks:

- **Length**: Answer must be at least 100 characters
- **Ending punctuation**: Must end with `.`, `!`, or `?`
- **Incomplete sentence patterns**: Detects common mid-sentence endings like:
  - Articles: "a", "an", "the"
  - Conjunctions: "and", "or", "but", "so"
  - Prepositions: "to", "for", "of", "in", "on", "at"
  - Verbs: "is", "are", "was", "were", "been"
  - Question words: "that", "which", "who", "what"
  - Modal verbs: "can", "will", "should", "might"

### 2. Updated Cache Logic

Both streaming and non-streaming answer generation now validate answers before caching:

```python
# New code - validates completeness
if _is_degraded_cached_answer(cache_payload):
    logger.info("Skipping cache PUT for degraded streaming answer to '%.80s'", question)
elif _is_incomplete_answer(full_answer):  # ✅ New check
    logger.warning("Skipping cache PUT for incomplete streaming answer to '%.80s' (answer ends: '...%.50s')",
                  question, full_answer[-50:] if full_answer else "")
else:
    cache.put(norm_q, query_embedding, cache_payload)
```

### 3. Integrated Cache Cleaning

Automatic cache cleaning is now integrated into:

**1. Application Startup** ([app/api/main.py](app/api/main.py)):
- Runs during the `_prewarm_cache()` startup task
- Cleans incomplete answers before prewarming with fresh content
- Happens automatically on every deploy/restart

**2. Manual Cache Prewarming** ([scripts/prewarm_cache.py](scripts/prewarm_cache.py)):
- Runs before prewarming questions
- Ensures cache is clean before adding new entries
- Invoked with: `python scripts/prewarm_cache.py`

**3. Utility Scripts** (for manual inspection/cleaning):
- **`scripts/clear_incomplete_cache.py`**: Clear a specific incomplete cached answer
- **`scripts/scan_incomplete_cache.py`**: Scan entire cache for incomplete answers and remove them
- **`scripts/test_incomplete_detection.py`**: Test suite for incomplete answer detection (12 test cases, all passing)

### 4. Added Cache Delete Method

Added `delete()` method to [app/qa/cache.py](app/qa/cache.py) to remove specific cache entries by normalized question:

```python
def delete(self, question: str) -> bool:
    """
    Delete a specific cache entry by normalized question.
    Returns True if entry was found and deleted, False otherwise.
    """
```

Removes from both in-memory cache and Redis persistence layer.

## Files Changed

1. **[app/qa/service.py](app/qa/service.py)**:
   - Added `_is_incomplete_answer()` function
   - Updated cache logic in `answer_question()` 
   - Updated cache logic in `answer_question_stream()`

2. **[app/qa/cache.py](app/qa/cache.py)**:
   - Added `delete()` method to remove specific cache entries
   - Fixed indentation in `clear()` method

3. **[app/api/main.py](app/api/main.py)**:
   - Added automatic incomplete cache cleaning to `_prewarm_cache()` startup function
   - Runs on every app startup/restart

4. **[scripts/prewarm_cache.py](scripts/prewarm_cache.py)**:
   - Added `clean_incomplete_cached_answers()` function
   - Integrated cache cleaning into prewarm workflow

5. **New utility scripts**:
   - [scripts/clear_incomplete_cache.py](scripts/clear_incomplete_cache.py)
   - [scripts/scan_incomplete_cache.py](scripts/scan_incomplete_cache.py)
   - [scripts/test_incomplete_detection.py](scripts/test_incomplete_detection.py)

## Testing

All 12 test cases pass, including:
- ✅ Detecting empty/too short answers
- ✅ Detecting answers without ending punctuation
- ✅ Detecting answers ending with articles, conjunctions, prepositions
- ✅ Detecting the specific "rest isn" incomplete answer pattern
- ✅ Allowing complete answers with proper endings
- ✅ Allowing answers with mid-sentence questions (properly ended)

## Production Deployment

### Automatic Cleaning

The fix includes **automatic cache cleaning** that runs:

1. **On every app startup/restart** - The `_prewarm_cache()` function in [app/api/main.py](app/api/main.py) automatically cleans incomplete answers before prewarming
2. **When manually prewarming** - Running `python scripts/prewarm_cache.py` cleans the cache first

### Manual Cleaning (Optional)

If you want to clean the cache immediately without waiting for a restart:

```bash
# Scan and optionally clean all incomplete cached answers
python scripts/scan_incomplete_cache.py

# Or clear a specific incomplete cached answer
python scripts/clear_incomplete_cache.py
```

After deployment, the fix will automatically:
- ✅ Prevent new incomplete answers from being cached
- ✅ Clean up existing incomplete answers on startup
- ✅ Clean up incomplete answers when prewarming cache

## Monitoring

The code now logs warnings when incomplete answers are skipped from caching:

```
WARNING: Skipping cache PUT for incomplete streaming answer to 'what does rest...' 
         (answer ends: '...it's clear that true rest isn')
```

Monitor these warnings to detect if streaming interruptions are becoming frequent, which may indicate network issues or OpenAI API timeouts.
