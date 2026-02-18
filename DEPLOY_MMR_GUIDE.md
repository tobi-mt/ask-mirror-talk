# 🚀 Deploy MMR Episode Diversity - Complete Guide

## Overview

**Version:** 2.1.0  
**Feature:** Maximal Marginal Relevance (MMR) for Episode Diversity  
**Impact:** Citations will show more diverse episodes instead of repeating the same 5 episodes

---

## Pre-Deployment Checklist

### ✅ Code Changes (Already Complete)
- [x] `app/qa/retrieval.py` - MMR algorithm implemented
- [x] `app/core/config.py` - `diversity_lambda` setting added
- [x] `.env.example` - `DIVERSITY_LAMBDA` documented
- [x] Frontend enhanced (v2.1.0) - Better loading & citations
- [x] All changes tested locally

### 📋 What You Need
- Railway project access
- Git repository access (GitHub/GitLab)
- WordPress theme access (for frontend files)

---

## Deployment Steps

### Step 1: Deploy Backend to Railway

#### Option A: Git Push (Recommended)
```bash
# 1. Commit all changes
git add .
git commit -m "feat: Add MMR episode diversity algorithm (v2.1.0)

- Implement Maximal Marginal Relevance for episode diversity
- Add DIVERSITY_LAMBDA config (default 0.7)
- Increase candidate pool from 18 to 30 chunks
- Enhance frontend loading animation and citation cards
- Update documentation and deployment guides"

# 2. Push to main branch
git push origin main
```

#### Option B: Manual Railway CLI
```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

#### Option C: Railway Dashboard
1. Go to Railway dashboard
2. Select your project
3. Click "Deploy" or trigger redeploy
4. Railway will auto-deploy from your Git repository

### Step 2: Configure Environment Variable

**Add to Railway Environment Variables:**

1. Go to Railway Dashboard → Your Project → Variables
2. Add new variable:
   - **Name:** `DIVERSITY_LAMBDA`
   - **Value:** `0.7`
   - **Description:** "MMR diversity balance (0.0=max diversity, 1.0=max relevance)"

3. Click "Add" and redeploy if needed

**Alternative Values to Consider:**
- `0.5` - Equal weight (50% relevance, 50% diversity) - More experimental
- `0.6` - Slightly more diversity (40% diversity)
- `0.7` - **Recommended default** (30% diversity, good balance)
- `0.8` - More conservative (20% diversity, mostly relevance)

### Step 3: Deploy Frontend to WordPress

Upload these 3 files to `/wp-content/themes/astra/`:

1. **ask-mirror-talk.css** (v2.1.0)
2. **ask-mirror-talk.js** (v2.1.0)
3. **ask-mirror-talk-standalone.php** (v2.1.0)

**Methods:**
- FTP/SFTP client (FileZilla, Cyberduck)
- cPanel File Manager
- WordPress file editor plugin

**Verify versions updated:**
```css
/* ask-mirror-talk.css */
/* Version: 2.1.0 */

/* ask-mirror-talk.js */
const CONFIG = {
  VERSION: '2.1.0',
  ...
}
```

---

## Post-Deployment Verification

### 1. Check Backend Deployment

**Railway Logs:**
```bash
railway logs
```

**Look for:**
```
✅ Database URL converted for psycopg3 compatibility
✅ Settings loaded: diversity_lambda=0.7
✅ Server started on port 8000
```

**Test API Health:**
```bash
curl https://your-railway-app.railway.app/health
```

Expected: `{"status": "ok"}`

### 2. Test MMR Algorithm

**Ask a test question:**
```bash
curl -X POST https://your-railway-app.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does Matt say about self-awareness?"}'
```

**Check logs for MMR output:**
```
MMR: Selected most relevant - Episode 123 (similarity: 0.854)
MMR: Selected diverse - Episode 456 (similarity: 0.782, MMR score: 0.650)
MMR: Selected diverse - Episode 789 (similarity: 0.756, MMR score: 0.625)
MMR: Final selection - 6 unique episodes from 30 candidates
```

### 3. Test Frontend

**Visit your WordPress page with the widget:**
1. Open browser console (F12)
2. Ask a question
3. Check for:
   - Beautiful loading animation appears
   - Citations load with enhanced cards
   - Excerpts are showing (first 150 chars)
   - Timestamps are styled buttons
   - No JavaScript errors

**Console should show:**
```
[Ask Mirror Talk] v2.1.0 initialized
[Ask Mirror Talk] Sending question: ...
[Ask Mirror Talk] Received answer with X citations
[Ask Mirror Talk] Citation #1: Episode "..." at 0:12:34
```

### 4. Verify Diversity

**Test with 3-5 different questions:**
- "What is self-awareness?"
- "How do I improve my relationships?"
- "What is the Hoffman Process?"

**Expected Results:**
- Each answer should reference **different episodes**
- ~33-50% overlap between questions (down from 83%)
- Mix of highly relevant + diverse episodes
- Always includes the most relevant match

**Track Episode IDs:**
| Question | Episode IDs Referenced |
|----------|------------------------|
| Question 1 | 12, 45, 78, 90, 102, 156 |
| Question 2 | 45, 67, 89, 134, 178, 201 |
| Question 3 | 34, 90, 112, 145, 167, 189 |

Notice: Some overlap (45, 90) but much more diversity!

---

## Monitoring & Tuning

### Week 1: Monitor User Feedback
- **Watch for:** User comments on episode variety
- **Collect:** Sample questions and their citations
- **Analyze:** Are users discovering new episodes?

### Week 2: Tune if Needed

**If users complain episodes are too random:**
```bash
# Increase lambda (more relevance)
DIVERSITY_LAMBDA=0.8
```

**If users still see repetitive episodes:**
```bash
# Decrease lambda (more diversity)
DIVERSITY_LAMBDA=0.6
```

**If answers feel less accurate:**
```bash
# Return to default
DIVERSITY_LAMBDA=0.7
```

### Check Railway Logs

**View real-time logs:**
```bash
railway logs --tail
```

**Look for patterns:**
```bash
railway logs | grep "MMR:"
```

**Count unique episodes:**
```bash
railway logs | grep "MMR: Final selection" | tail -20
```

---

## Rollback Plan

### If Issues Arise

**1. Revert Diversity Lambda:**
```bash
# In Railway, set:
DIVERSITY_LAMBDA=1.0
# This disables diversity bonus, pure relevance
```

**2. Revert Code (if needed):**
```bash
# Find previous commit
git log --oneline

# Revert to previous version
git revert HEAD

# Push
git push origin main
```

**3. Revert Frontend:**
- Upload old versions of JS/CSS files (v2.0.x)

---

## Success Metrics

### Expected Improvements

**Episode Diversity:**
- ✅ Before: 5 episodes in 83% of queries
- ✅ After: ~33-50% overlap (33-50 unique episodes showing up more)

**User Engagement:**
- ✅ More episodes discovered
- ✅ Users explore more content
- ✅ Increased audio playback from citations

**System Performance:**
- ✅ No impact on latency (still ~300-500ms)
- ✅ Same memory usage
- ✅ Same database load

---

## Troubleshooting

### Problem: Citations still repetitive

**Check:**
1. Is `DIVERSITY_LAMBDA` set in Railway?
2. Are you testing with very similar questions?
3. Check logs for MMR selection process

**Fix:**
```bash
# Lower lambda for more diversity
DIVERSITY_LAMBDA=0.5

# Or check candidate pool size in logs
railway logs | grep "candidates"
```

### Problem: Answers feel less accurate

**Check:**
1. Is lambda too low (< 0.6)?
2. Are users asking very specific questions?

**Fix:**
```bash
# Increase lambda for more relevance
DIVERSITY_LAMBDA=0.8
```

### Problem: Deployment failed

**Check Railway logs:**
```bash
railway logs
```

**Common issues:**
- Missing dependency (check `requirements.txt`)
- Database connection error (check `DATABASE_URL`)
- Port binding issue (Railway auto-assigns)

**Fix:**
```bash
# Redeploy
railway up --detach
```

### Problem: Frontend not updating

**Check:**
1. Browser cache cleared? (Ctrl+Shift+R)
2. Correct files uploaded to WordPress?
3. File permissions (should be 644)

**Fix:**
```bash
# Clear browser cache
# Or add version query param in PHP:
# ?ver=2.1.0
```

---

## Advanced Tuning (Optional)

### Embedding-Based Diversity

For even better diversity, you can enhance the MMR algorithm to use embedding similarity:

```python
# In app/qa/retrieval.py
# Calculate diversity using cosine distance between embeddings
diversity_score = min([
    chunk.embedding.cosine_distance(selected_chunk.embedding)
    for selected_chunk, _ in selected
])
```

**Trade-off:** More CPU, better diversity

### Temporal Decay

Prefer recent episodes:

```python
# Add recency bonus
import datetime
days_old = (datetime.now() - episode.published_date).days
recency_bonus = 1.0 / (1.0 + days_old / 365)  # Decay over 1 year

mmr_score += (0.1 * recency_bonus)
```

**Trade-off:** Biases toward recent content

### Category Diversity

If you tag episodes by topic:

```python
# Penalize same category
seen_categories = {selected_chunk.episode.category}
if chunk.episode.category not in seen_categories:
    diversity_bonus += 0.2
```

**Trade-off:** Requires category metadata

---

## Documentation Updates

### Update After Deployment

**README.md:**
- Add "Episode Diversity with MMR" to features
- Document `DIVERSITY_LAMBDA` setting

**CHANGELOG.md:**
```markdown
## [2.1.0] - 2024-XX-XX
### Added
- MMR algorithm for episode diversity in citations
- DIVERSITY_LAMBDA config for tuning relevance/diversity balance
- Enhanced frontend loading animation and citation cards
- Episode excerpt display in citation cards

### Changed
- Increased candidate pool from 18 to 30 chunks
- Citations now show more diverse episodes (33-50% overlap vs 83%)

### Fixed
- Repetitive episode references in answers
```

---

## Next Steps

After successful deployment:

1. ✅ **Week 1:** Monitor logs and user feedback
2. ✅ **Week 2:** Tune `DIVERSITY_LAMBDA` if needed (0.5-0.8 range)
3. ✅ **Week 3:** Analyze episode coverage in logs
4. ✅ **Week 4:** Consider advanced tuning (embedding diversity, temporal decay)
5. ✅ **Month 2:** Evaluate user engagement metrics

**Questions to Track:**
- Are users discovering more episodes?
- Are they clicking on citations more?
- Are answer quality/relevance maintained?
- Any complaints about episode variety?

---

## Support & Resources

**Documentation:**
- `MMR_IMPLEMENTATION_COMPLETE.md` - Technical details
- `VERSION_2.1.0_READY.md` - Frontend changes
- `EPISODE_DIVERSITY_ISSUE.md` - Original problem analysis

**Logs:**
```bash
# Railway
railway logs --tail

# Local testing
docker-compose logs -f api
```

**Contact:**
- Check GitHub issues for community help
- Railway support for deployment issues
- WordPress forums for theme/plugin conflicts

---

## Summary

**What's Deployed:**
- ✅ MMR algorithm for episode diversity
- ✅ Configurable diversity via `DIVERSITY_LAMBDA`
- ✅ Enhanced frontend (v2.1.0)
- ✅ Better loading animation
- ✅ Improved citation cards

**Expected Impact:**
- 🎯 More diverse episode citations
- 🎯 Users discover more of your 471 episodes
- 🎯 Better user engagement and exploration
- 🎯 Maintained answer quality and relevance

**Default Settings:**
- `DIVERSITY_LAMBDA=0.7` (70% relevance, 30% diversity)
- `TOP_K=6` (6 citations per answer)
- `MIN_SIMILARITY=0.15` (quality threshold)

**Ready to deploy!** 🚀
