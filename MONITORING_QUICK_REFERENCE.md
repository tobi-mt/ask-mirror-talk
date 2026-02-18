# 📊 Monitoring Quick Reference Card

## ✅ What's Working Now

### Backend (Railway Production)
- ✅ MMR algorithm deployed and working
- ✅ 88.9% episode diversity achieved
- ✅ API responding correctly
- ✅ Logging MMR selection decisions

### Monitoring Scripts
- ✅ Daily log analysis: `./scripts/analyze_daily_logs.sh`
- ✅ Weekly reports: `python scripts/weekly_engagement_report.py`
- ⚠️ Episode analytics: Requires production DB access

---

## 🚀 Daily Monitoring (2 minutes)

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
./scripts/analyze_daily_logs.sh
```

**What it shows:**
- Total queries in last 24h
- Top 10 most cited episodes
- Unique episodes cited
- MMR candidate pool usage
- Error count
- API health status

**Good indicators:**
- ✅ Queries > 0
- ✅ Unique episodes > 10/day
- ✅ No errors
- ✅ API health: {"status": "ok"}

---

## 📈 Weekly Report (10 minutes)

```bash
source .venv/bin/activate
python scripts/weekly_engagement_report.py > reports/week_$(date +%Y%m%d).txt
```

**Then fill in manually:**
1. Query volume (from Railway logs)
2. Unique episodes cited
3. Episode distribution
4. User feedback

**Target metrics:**
- Unique episodes: >100/week (out of 471 total)
- Top episode: <20% of queries
- User feedback: Positive

---

## 🔍 Manual Log Queries

### Railway Logs (Real-time)

```bash
# Live logs with MMR filtering
railway logs --tail | grep "MMR:"

# Total queries this week
railway logs --since 7d | grep "POST /ask" | wc -l

# Unique episodes this week  
railway logs --since 7d | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq | wc -l

# Top 10 episodes this week
railway logs --since 7d | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq -c | sort -rn | head -10

# Check for errors
railway logs --since 24h | grep "ERROR"

# MMR performance
railway logs --since 7d | grep "MMR: Final selection" | tail -20
```

---

## 🧪 Quick API Tests

### Health Check
```bash
curl https://ask-mirror-talk-production.up.railway.app/health
```
Expected: `{"status": "ok"}`

### Test Episode Diversity
```bash
# Test 3 different questions
for q in "self-awareness" "leadership" "relationships"; do
  echo "Question: $q"
  curl -s -X POST https://ask-mirror-talk-production.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$q\"}" \
    | jq -r '.citations[].episode_id'
  echo ""
done
```

Expected: Different episode IDs for each question

---

## 📊 Key Metrics Dashboard

| Metric | Target | How to Check |
|--------|--------|--------------|
| **Diversity Rate** | >70% | Unique episodes / Total citations |
| **Episode Overlap** | <50% | Compare episodes across queries |
| **Unique Episodes/Week** | >100 | `railway logs --since 7d \| grep "MMR: Selected" \| ... \| wc -l` |
| **Top Episode %** | <20% | Count / Total queries |
| **Error Rate** | <1% | Errors / Total requests |
| **API Uptime** | >99% | Health check status |

---

## ⚠️ Alert Thresholds

### 🚨 Critical (Act Immediately)
- Error rate > 5%
- API down > 5 minutes
- One episode > 50% of queries
- Response time > 5 seconds

### ⚡ Warning (Review Within 24h)
- Query volume drops > 30%
- Unique episodes < 50/week
- Top episode > 30% of queries
- Multiple negative feedback

### ℹ️ Info (Weekly Review)
- Query volume increases >50%
- New patterns emerging
- Seasonal trends

---

## 🔧 Tuning Guide

### Current Setting
```
DIVERSITY_LAMBDA = 0.7 (default in code)
Result: 88.9% diversity ✅
```

### If Users Complain: "Too Repetitive"
```bash
# Railway Dashboard → Variables
DIVERSITY_LAMBDA=0.6  # More diversity
```

### If Users Complain: "Not Relevant"
```bash
# Railway Dashboard → Variables
DIVERSITY_LAMBDA=0.8  # More relevance
```

### If Everything is Perfect (Current State!)
```bash
# Keep default 0.7 or don't set the variable
# Working great as-is! ✅
```

---

## 📁 Important Files

### Documentation
- `COMPLETE_DEPLOYMENT_SUMMARY.md` - Full deployment overview
- `USER_ENGAGEMENT_MONITORING.md` - Complete monitoring guide  
- `MMR_TEST_RESULTS_SUCCESS.md` - Test results (88.9% diversity!)
- `DEPLOYMENT_STATUS_V2.1.0.md` - Deployment verification

### Scripts
- `scripts/analyze_daily_logs.sh` - Daily monitoring
- `scripts/weekly_engagement_report.py` - Weekly template
- `scripts/analyze_episode_engagement.py` - DB analytics (needs prod DB)
- `scripts/test_mmr_diversity.py` - MMR testing

### Reports
- `reports/` - Save your weekly/daily reports here

---

## 🎯 Success Indicators

### ✅ System is Healthy
- Unique episodes: >100/week
- No episode dominates (<20%)
- No errors in logs
- Positive user feedback
- Query volume stable/growing

### ⚠️ Needs Attention
- Unique episodes: <50/week
- One episode: >40% of queries
- Errors appearing
- Negative user feedback
- Query volume declining

---

## 💡 Pro Tips

1. **Daily:** Quick glance at `./scripts/analyze_daily_logs.sh`
2. **Weekly:** Fill in report template, track trends
3. **Monthly:** Review and plan improvements
4. **Always:** Monitor user feedback channels

---

## 🆘 Troubleshooting

### Episode Analytics Script Won't Run
**Issue:** Trying to connect to local database  
**Solution:** Script requires production DATABASE_URL  
**Alternative:** Use Railway logs for monitoring instead

### Railway Logs Command Not Found
**Issue:** Railway CLI not installed  
**Solution:** `npm i -g @railway/cli` then `railway login`

### No Queries in Logs
**Issue:** New deployment or low traffic  
**Solution:** Normal for new deployments, monitor over time

---

## 📞 Quick Support

**Documentation:** See markdown files in project root  
**Logs:** `railway logs --tail`  
**Health:** `curl https://ask-mirror-talk-production.up.railway.app/health`  
**Test:** See "Quick API Tests" section above

---

**Last Updated:** February 18, 2026  
**Version:** 2.1.0  
**Status:** ✅ Production Ready

**Your monitoring system is ready to use!** 🎉
