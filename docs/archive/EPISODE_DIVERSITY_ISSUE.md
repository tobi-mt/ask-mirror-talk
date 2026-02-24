# 🔍 Episode Diversity Issue - Analysis & Solutions

## Problem Identified ✅

**User Feedback:** "Referenced episodes are mostly always the same"

**Testing Results:**
```
Question 1 (Leadership):      Episodes: 10, 6, 77, 2, 95, 101
Question 2 (Personal Growth): Episodes: 10, 6, 95, 101, 62, 77
Question 3 (Relationships):   Episodes: 10, 6, 95, 101, 5, 77
```

**Pattern:**
- 5 episodes appear in ALL queries: 10, 6, 95, 101, 77
- Only 1-2 episodes change based on the question
- **471 episodes available**, but same ~5 dominate results

---

## Root Cause

### Issue: "Universal Relevance" Bias

Certain episodes have very **general, high-level themes** that semantically match almost any question:

**Examples:**
- **Episode 10**: "The Ripple Effect: How Small Choices Create Lasting Hope"
  - Generic themes: choices, hope, life changes
  - Matches: leadership, purpose, relationships, growth...
  
- **Episode 95**: "From Betrayal to Breakthrough through Healing and Transformation"
  - Generic themes: transformation, healing, breakthrough
  - Matches: almost any personal development question

These episodes contain universal wisdom that the embedding model rates as highly similar to many different queries, even when more specific episodes would be better.

---

## Solutions

### Option 1: Add Recency Boost (Quick Fix) ⚡

Favor newer episodes slightly to increase diversity over time.

**Pros:**
- ✅ Easy to implement
- ✅ Ensures users see different content over time
- ✅ Highlights recent episodes

**Cons:**
- ⚠️ May miss highly relevant older episodes
- ⚠️ Recency doesn't equal relevance

### Option 2: MMR (Maximal Marginal Relevance) 🎯 RECOMMENDED

Balance relevance with diversity - don't just pick top 6 most similar, pick most similar PLUS diverse.

**How it works:**
1. Get top 18 most similar chunks (3x top_k)
2. Pick #1 (most relevant)
3. For each remaining slot, pick chunk that is:
   - **Relevant** to query (high similarity)
   - **Different** from already selected episodes
4. This ensures variety while maintaining quality

**Pros:**
- ✅ Maintains high relevance
- ✅ Increases diversity
- ✅ Better user experience
- ✅ Standard practice in semantic search

**Cons:**
- ⚠️ Slightly more complex
- ⚠️ Requires diversity calculation

### Option 3: Category-Based Sampling 📊

Group episodes by topic/domain, ensure we pull from different categories.

**Pros:**
- ✅ Guarantees topical diversity
- ✅ Exposes users to different areas

**Cons:**
- ⚠️ Requires episode categorization
- ⚠️ More complex setup

### Option 4: Temporal Diversity 📅

Don't show same episode if it was in recent queries (track per-user or session).

**Pros:**
- ✅ Great user experience
- ✅ Each query feels fresh

**Cons:**
- ⚠️ Requires session/user tracking
- ⚠️ More infrastructure

---

## Recommended Solution: MMR (Option 2)

### Implementation Plan

**File to Edit:** `app/qa/retrieval.py`

**Changes:**
1. Retrieve top 18 chunks (instead of 18 via top_k * 3)
2. Implement MMR algorithm:
   - Select most relevant chunk
   - For remaining slots, balance similarity + diversity
3. Use lambda parameter to control relevance vs diversity trade-off

**Code:**
```python
def retrieve_chunks_with_diversity(db: Session, query_embedding: list[float], lambda_param: float = 0.7):
    """
    Retrieve chunks using MMR for diversity.
    
    Args:
        lambda_param: 0.0 = max diversity, 1.0 = max relevance (default 0.7)
    """
    # Get more candidates than needed
    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, distance.label("distance"))
        .order_by(distance.asc())
        .limit(settings.top_k * 3)  # Get 18 candidates for 6 slots
    )
    candidates = db.execute(stmt).all()
    
    # Filter by minimum similarity
    candidates = [
        (chunk, 1 - float(dist)) 
        for chunk, dist in candidates 
        if (1 - float(dist)) >= settings.min_similarity
    ]
    
    if not candidates:
        return []
    
    # MMR algorithm
    selected = []
    seen_episodes = set()
    
    # Pick the most relevant first
    best_chunk, best_sim = candidates[0]
    selected.append((best_chunk, best_sim))
    seen_episodes.add(best_chunk.episode_id)
    
    # For remaining slots, balance relevance + diversity
    while len(selected) < settings.top_k and len(candidates) > len(selected):
        best_score = -1
        best_candidate = None
        
        for chunk, similarity in candidates:
            # Skip if from same episode
            if chunk.episode_id in seen_episodes:
                continue
            
            # Calculate diversity (how different from selected chunks)
            min_diversity = 1.0
            for selected_chunk, _ in selected:
                # Use episode_id difference as proxy for diversity
                # Could use embedding distance for more precision
                if chunk.episode_id != selected_chunk.episode_id:
                    diversity = 1.0  # Different episode = diverse
                else:
                    diversity = 0.0
                min_diversity = min(min_diversity, diversity)
            
            # MMR score: balance relevance and diversity
            mmr_score = lambda_param * similarity + (1 - lambda_param) * min_diversity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_candidate = (chunk, similarity)
        
        if best_candidate:
            selected.append(best_candidate)
            seen_episodes.add(best_candidate[0].episode_id)
        else:
            break
    
    return selected
```

---

## Quick Win: Adjust Existing Logic

**Even simpler fix** - just increase the candidate pool:

```python
# Current: Get 3x candidates (18 for 6 results)
.limit(settings.top_k * 3)

# Better: Get 5x candidates (30 for 6 results)
.limit(settings.top_k * 5)
```

This gives more options for deduplication, increasing chance of variety.

---

## Testing Plan

After implementing MMR:

```bash
# Test 1: Same question multiple times
for i in {1..3}; do
  curl -X POST .../ask -d '{"question": "leadership"}' | jq '.citations[].episode_id'
done

# Should see different episodes each time (or at least some variety)

# Test 2: Different questions
curl -X POST .../ask -d '{"question": "purpose"}' | jq '.citations[].episode_id'
curl -X POST .../ask -d '{"question": "relationships"}' | jq '.citations[].episode_id'
curl -X POST .../ask -d '{"question": "career"}' | jq '.citations[].episode_id'

# Should see LESS overlap than current 5/6 episodes
```

**Success Criteria:**
- ✅ Different questions show <50% overlap (currently ~83%)
- ✅ Same question shows variety if asked multiple times
- ✅ Responses still feel relevant and helpful
- ✅ Users discover more episodes

---

## Recommendation

**Start with Quick Win:**
1. Change `top_k * 3` to `top_k * 5` in `retrieval.py`
2. Deploy and test
3. Monitor user feedback

**Then implement MMR:**
1. Add MMR algorithm to `retrieval.py`
2. Set `lambda_param = 0.7` (70% relevance, 30% diversity)
3. Test and tune based on results

**Finally, consider:**
- Episode freshness boost
- Session-based diversity tracking
- User feedback on citation quality

---

## Impact

**Current:**
- 5/6 episodes same across different questions
- Users see same content repeatedly
- ~471 episodes underutilized

**After MMR:**
- 2-3/6 episodes overlap (estimate)
- More episode discovery
- Better use of full catalog
- Improved user experience

**User Benefit:**
- "Every question feels fresh!"
- "I'm discovering new episodes I never knew existed"
- "The references are more specific to my question"

---

**Want me to implement the MMR solution?** 🚀
