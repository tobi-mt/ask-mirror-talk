# 🚀 Deployment Status - v2.1.0 MMR Episode Diversity

## ✅ BACKEND DEPLOYED

**Date:** February 18, 2026  
**Commit:** e0ea025  
**Status:** Code pushed to Bitbucket → Railway auto-deploying

---

## What Was Deployed

### Backend Changes (Railway)
- ✅ MMR algorithm in `app/qa/retrieval.py`
- ✅ `diversity_lambda` config in `app/core/config.py`
- ✅ Updated `.env.example` with documentation
- ✅ Test script `scripts/test_mmr_diversity.py`
- ✅ Complete documentation set

### Algorithm Details
- **Candidate Pool:** Increased from 18 to 30 chunks (5x top_k)
- **Selection:** MMR balances relevance (70%) + diversity (30%)
- **Default Lambda:** 0.7 (configurable via env var)
- **Logging:** Added MMR selection tracking

---

## NEXT STEPS

### 1. Configure Railway Environment Variable (OPTIONAL)

Railway will use the default `diversity_lambda = 0.7` from the code. If you want to customize:

**Go to Railway Dashboard:**
1. Select your project
2. Go to Variables tab
3. Add new variable:
   - **Name:** `DIVERSITY_LAMBDA`
   - **Value:** `0.7` (or 0.5-0.9 to tune)
   - **Description:** "MMR diversity: 0.0=max diversity, 1.0=max relevance"

**Tuning Guide:**
- `0.5` - Maximum diversity (50/50 split)
- `0.6` - More diversity
- `0.7` - **Recommended default** (balanced)
- `0.8` - More relevance
- `0.9` - Maximum relevance

### 2. Monitor Deployment

**Check Railway Logs:**
```bash
# Watch deployment
railway logs --tail

# Look for:
# ✅ "Settings loaded: diversity_lambda=0.7"
# ✅ "MMR: Selected most relevant - Episode X"
# ✅ "MMR: Final selection - 6 unique episodes from 30 candidates"
```

**Test Health Endpoint:**
```bash
curl https://ask-mirror-talk-production.up.railway.app/health
# Expected: {"status": "ok"}
```

### 3. Test MMR Algorithm

**Quick Test:**
```bash
curl -X POST https://ask-mirror-talk-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does Matt say about self-awareness?"}' \
  | jq '.citations[] | "\(.episode_id): \(.episode_title)"'
```

**Run Multiple Tests:**
```bash
# Test same question 3 times - should see variety
for i in {1..3}; do
  echo "Test $i:"
  curl -s -X POST https://ask-mirror-talk-production.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "leadership"}' \
    | jq -r '.citations[].episode_id'
  echo ""
done
```

**Test Different Topics:**
```bash
questions=("self-awareness" "relationships" "meditation" "career" "emotions")

for q in "${questions[@]}"; do
  echo "Question: $q"
  curl -s -X POST https://ask-mirror-talk-production.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$q\"}" \
    | jq -r '.citations[].episode_id' | sort | uniq
  echo ""
done

# Expected: Less overlap than before (33-50% vs 83%)
```

### 4. Frontend Deployment (WordPress)

**Files to Upload:**
Located in: `/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/`

Upload to WordPress `/wp-content/themes/astra/`:
1. `ask-mirror-talk-standalone.php` (v2.1.0)
2. `ask-mirror-talk.js` (v2.1.0)
3. `ask-mirror-talk.css` (v2.1.0)

**Update `functions.php`:**
```php
// Ensure this line is present (without leading slash):
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php';
```

**Clear Caches:**
- Browser: Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- WordPress: Clear all caches
- Test in Incognito mode

**Verify Frontend:**
1. Open browser console (F12)
2. Load the widget page
3. Look for: `[Ask Mirror Talk] v2.1.0 initialized`
4. Ask a question
5. Check:
   - Loading animation appears (spinning circle)
   - Citations display as styled cards
   - Episode excerpts showing
   - Timestamp buttons styled
   - Hover effects working

---

## Expected Results

### Before v2.1.0
```
Same 5 episodes in ~83% of all queries
Episodes 10, 6, 95, 101, 77 dominated
Users: "Always the same episodes"
```

### After v2.1.0
```
~33-50% overlap between different questions
No single episode dominates
Users discover new episodes
More engagement with citation diversity
```

### Success Metrics

**Diversity:**
- [ ] Different questions show <50% overlap (currently ~83%)
- [ ] Same question shows variety when asked multiple times
- [ ] No single episode appears in >30% of queries

**Quality:**
- [ ] Top result always highly relevant (similarity >0.6)
- [ ] Average similarity remains high (>0.3)
- [ ] Answers still feel accurate and helpful

**User Experience:**
- [ ] Users report discovering new episodes
- [ ] Citation click-through rates increase
- [ ] No complaints about irrelevant results

---

## Monitoring Schedule

### Week 1: Initial Observation
- Monitor Railway logs for MMR selection patterns
- Track user feedback on episode variety
- Note any relevance complaints
- Test with multiple questions daily

### Week 2-4: Analysis & Tuning
- Analyze episode coverage in logs
- Calculate actual diversity metrics
- Tune `DIVERSITY_LAMBDA` if needed:
  - Too repetitive? → Decrease to 0.6
  - Too random? → Increase to 0.8

### Month 2+: Long-term Evaluation
- Track citation click-through rates
- Monitor episode discovery patterns
- Analyze user engagement metrics
- Consider advanced enhancements (embedding-based diversity, temporal decay)

---

## Troubleshooting

### Issue: Still seeing repetitive episodes

**Diagnosis:**
```bash
railway logs | grep "MMR: Final selection"
# Check if diversity is actually running
```

**Fix:**
```bash
# Decrease lambda for more diversity
DIVERSITY_LAMBDA=0.6

# Or restart Railway service
```

### Issue: Answers less relevant

**Diagnosis:**
```bash
railway logs | grep "similarity:"
# Check if similarities are too low
```

**Fix:**
```bash
# Increase lambda for more relevance
DIVERSITY_LAMBDA=0.8
```

### Issue: Deployment failed

**Check:**
```bash
railway logs
# Look for errors
```

**Common fixes:**
- Redeploy from Railway dashboard
- Check DATABASE_URL is set
- Verify psycopg compatibility

---

## Rollback Plan

### Quick Rollback (No Code Changes)
```bash
# Set lambda to 1.0 (pure relevance, disables diversity)
DIVERSITY_LAMBDA=1.0
# Railway auto-restarts
```

### Full Rollback (Revert Code)
```bash
git revert e0ea025
git push origin main
# Railway auto-deploys previous version
```

---

## Documentation Reference

- `DEPLOY_MMR_GUIDE.md` - Complete deployment guide
- `MMR_IMPLEMENTATION_COMPLETE.md` - Technical implementation details
- `EPISODE_DIVERSITY_ISSUE.md` - Problem analysis and root cause
- `V2.1.0_COMPLETE_PACKAGE.md` - Complete package overview
- `scripts/test_mmr_diversity.py` - Automated testing script

---

## Summary

**Status:** ✅ Backend deployed to Railway

**What's Live:**
- MMR episode diversity algorithm
- Configurable diversity tuning
- Enhanced logging

**What's Pending:**
- Railway environment variable (optional)
- Frontend WordPress upload
- User testing and feedback

**Next Action:**
1. Monitor Railway deployment logs
2. Test API with curl commands above
3. Upload frontend files to WordPress
4. Monitor user feedback

---

**Deployment successful! 🎉**

Watch the logs and test the API to verify MMR is working correctly.
