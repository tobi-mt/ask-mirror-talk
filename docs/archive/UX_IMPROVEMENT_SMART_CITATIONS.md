# 🎯 User Experience Improvement: Smart Episode Citations

**Date:** February 20, 2026  
**Status:** ✅ Implemented  
**Impact:** High - Significantly improves episode discovery and user engagement

## 🎁 What Changed

### Before
When users asked: **"How to overcome addiction"**

**Citations showed:**
- 6 random chunks from the database
- Might be from 6 different episodes OR all from 1-2 episodes
- No guarantee of topical relevance
- Hard to know which episodes are most important

**Example:**
```
Citations (6 chunks):
1. Episode A - Chunk about relationships (15:30)
2. Episode A - Chunk about fear (23:45)
3. Episode B - Chunk about addiction ✓ (5:00)
4. Episode C - Chunk about success (18:20)
5. Episode D - Chunk about trauma (32:10)
6. Episode B - Chunk about recovery ✓ (42:30)
```
Only 2/6 citations are directly about the question!

---

### After
When users ask: **"How to overcome addiction"**

**Citations show:**
- **Top 5 most relevant episodes** specifically about addiction
- Each episode scored by relevance to the question
- Best timestamp shown for each episode
- Guaranteed episode diversity (5 unique episodes)

**Example:**
```
Top 5 Relevant Episodes:
1. "Overcoming Porn Addiction: A Personal Journey" [12:30] (95% relevance)
2. "Breaking Free from Fear to Live Authentically" [8:15] (82% relevance)
3. "From Pain to Purpose with Jordan Power" [15:00] (78% relevance)
4. "Childhood Trauma and Single Motherhood" [22:45] (71% relevance)
5. "Mental Health and Recovery" [6:30] (69% relevance)
```
All 5 episodes are directly about the question!

## 🔧 How It Works

### Two-Tier Approach

**Tier 1: Comprehensive Answer Generation**
- Retrieves 6-10 diverse chunks using MMR (Maximal Marginal Relevance)
- Ensures the ANSWER has comprehensive coverage
- Includes different perspectives and complementary insights

**Tier 2: Smart Episode Selection**
- Groups chunks by episode
- Calculates episode-level relevance score:
  - 60% - Best chunk similarity (peak relevance)
  - 30% - Average similarity (consistency)
  - 10% - Coverage (number of relevant chunks)
- Selects top 5 episodes
- Shows best timestamp in each episode

### Episode Scoring Example

Question: "How to overcome addiction"

```
Episode A: "Overcoming Porn Addiction"
  - Chunk 1: 0.92 similarity
  - Chunk 2: 0.88 similarity
  - Chunk 3: 0.85 similarity
  → Relevance Score: 0.60*0.92 + 0.30*0.88 + 0.10*0.6 = 0.876

Episode B: "Building Confidence"
  - Chunk 1: 0.45 similarity
  - Chunk 2: 0.38 similarity
  → Relevance Score: 0.60*0.45 + 0.30*0.41 + 0.10*0.4 = 0.433

Episode A ranks higher → Gets cited
```

## 📊 Benefits

### For Users
1. **Clearer Discovery** - Immediately see which episodes are most relevant
2. **Better Listening Experience** - Start at the exact timestamp for the topic
3. **Confidence** - Know you're getting the best episodes for your question
4. **Time Savings** - Don't waste time on tangentially related content

### For Engagement
1. **Higher Click-Through** - Users more likely to listen to relevant episodes
2. **Better Retention** - Episodes match expectations (no bait-and-switch)
3. **Increased Discovery** - Users find more related content within cited episodes
4. **Stronger Recommendations** - "If you liked this answer, check out these 5 episodes"

### For Analytics
1. **Topic Clustering** - Understand which episodes cover which topics
2. **Content Gaps** - Identify topics with few relevant episodes
3. **Quality Metrics** - Track which episodes get cited most often
4. **User Behavior** - See which cited episodes actually get listened to

## 🎚️ Configuration

### Default Settings (In .env or Railway)
```bash
# Maximum cited episodes (default: 5, recommended: 3-7)
MAX_CITED_EPISODES=5

# Minimum similarity for inclusion (unchanged)
MIN_SIMILARITY=0.15

# Diversity for answer generation (unchanged)
DIVERSITY_LAMBDA=0.7
```

### Tuneable Parameters

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `max_cited_episodes` | 5 | Number of episodes to cite | More = more discovery, Less = more focused |
| `min_similarity` | 0.15 | Minimum relevance threshold | Higher = stricter matching |
| `diversity_lambda` | 0.7 | Answer diversity (MMR) | Lower = more diverse answer |

**Recommendation:** Keep `max_cited_episodes=5`
- Provides good coverage without overwhelming users
- Balances discovery with focus
- Most questions have 5+ relevant episodes

## 🧪 Testing

### Quick Test
```bash
# Run the test script
python scripts/test_smart_citations.py
```

This will test with 5 sample questions and compare legacy vs. smart citations.

### Manual Test via API
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to overcome addiction"}'
```

### What to Look For
✅ Exactly 5 unique episodes in citations (or fewer if <5 relevant episodes exist)  
✅ Episode titles all relate to the question topic  
✅ Each episode has a valid timestamp  
✅ Relevance scores decrease from #1 to #5  
✅ Answer is comprehensive (uses more than just the 5 cited episodes)

## 📈 Success Metrics to Track

### Immediate (Week 1)
- [ ] Average number of unique episodes cited per question
- [ ] Distribution of relevance scores for cited episodes
- [ ] Percentage of questions with 5+ highly relevant episodes (>70% similarity)

### Short-term (Month 1)
- [ ] Click-through rate on episode citations (before vs. after)
- [ ] Average time spent listening to cited episodes
- [ ] User feedback on episode relevance

### Long-term (Month 3+)
- [ ] Repeat listening rate (users coming back for more episodes)
- [ ] Episode discovery patterns (do users explore beyond citations?)
- [ ] Content gaps identified (topics needing more episodes)

## 🚀 Deployment

### Files Changed
1. ✅ `app/qa/smart_citations.py` - New file (episode selection logic)
2. ✅ `app/qa/service.py` - Updated (two-tier retrieval)
3. ✅ `app/qa/answer.py` - Updated (citation override support)
4. ✅ `app/core/config.py` - Updated (max_cited_episodes setting)
5. ✅ `scripts/test_smart_citations.py` - New file (testing)

### Deployment Steps
1. ✅ Code implemented and tested locally
2. ⏳ Commit changes to git
3. ⏳ Push to production
4. ⏳ Monitor initial responses
5. ⏳ Gather user feedback
6. ⏳ Tune parameters if needed

### Rollback Plan
If issues arise:
```python
# In app/qa/service.py, change default:
def answer_question(db, question, user_ip, use_smart_citations=False):
    ...
```

Or set environment variable:
```bash
USE_SMART_CITATIONS=false
```

## 🔮 Future Enhancements

### Phase 2: Multiple Timestamps Per Episode
Show multiple relevant segments within the same episode:
```
"Overcoming Porn Addiction" episode:
  - 5:30 - Introduction to the struggle
  - 15:45 - Practical recovery strategies
  - 32:10 - Maintaining long-term sobriety
```

### Phase 3: Episode Clustering
Group similar episodes:
```
Addiction Recovery (3 episodes):
  - "Overcoming Porn Addiction"
  - "Breaking Free from Fear"
  - "From Pain to Purpose"

Trauma and Healing (2 episodes):
  - "Childhood Trauma"
  - "Mental Health and Recovery"
```

### Phase 4: Relevance Explanations
Show why each episode was selected:
```
1. "Overcoming Porn Addiction" [12:30]
   → Cited because: Directly discusses addiction recovery process
   
2. "Breaking Free from Fear" [8:15]
   → Cited because: Covers the psychological barriers to recovery
```

## 💡 Key Insights

1. **Quality > Quantity** - 5 highly relevant episodes > 6 random chunks
2. **User Trust** - When citations match the question, users trust the system more
3. **Discovery Path** - Good citations create a natural path for deeper exploration
4. **Content Strategy** - Analytics reveal which topics need more episode coverage

---

**Implementation Complete!** 🎉

**Next Actions:**
1. Test with the provided test script
2. Deploy to production
3. Monitor user engagement metrics
4. Gather feedback for future improvements

**Questions or Issues?**
- Check `SMART_EPISODE_CITATIONS.md` for technical details
- Run `python scripts/test_smart_citations.py` for testing
- Review logs for episode selection reasoning
