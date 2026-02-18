# 📊 Monitoring Tools - Quick Start

This directory contains tools for monitoring user engagement and episode diversity.

## Quick Commands

### Daily Health Check
```bash
# Run daily monitoring
./scripts/analyze_daily_logs.sh

# Save to file
./scripts/analyze_daily_logs.sh > reports/daily_$(date +%Y%m%d).txt
```

### Weekly Report
```bash
# Generate weekly report template
python scripts/weekly_engagement_report.py

# Save and fill in manually
python scripts/weekly_engagement_report.py > reports/week_$(date +%Y%m%d).txt
```

### Episode Analytics
```bash
# Analyze episode engagement in database
python scripts/analyze_episode_engagement.py
```

### Manual Log Queries
```bash
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

## Monitoring Schedule

### Daily (Automated - Recommended)
```bash
# Add to crontab (runs every day at 9am)
crontab -e

# Add this line:
0 9 * * * cd /path/to/ask-mirror-talk && ./scripts/analyze_daily_logs.sh >> reports/daily_log.txt 2>&1
```

### Weekly (Manual)
- Monday morning: Run weekly report
- Review episode diversity metrics
- Check user feedback channels
- Test with 3-5 sample questions

### Monthly (Strategic)
- Compare month-over-month trends
- Analyze seasonal patterns
- Review DIVERSITY_LAMBDA tuning
- Plan improvements

## Key Metrics

**Target Goals:**
- ✅ Unique episodes: >100/week (out of 471)
- ✅ Top episode: <20% of queries
- ✅ Error rate: <1%
- ✅ Diversity rate: >80%

**Warning Signs:**
- ⚠️ Unique episodes: <50/week
- ⚠️ One episode: >40% of queries
- ⚠️ Error rate: >5%
- ⚠️ Negative user feedback

## Files

- `analyze_daily_logs.sh` - Daily Railway log analysis
- `analyze_episode_engagement.py` - Database episode analytics
- `weekly_engagement_report.py` - Weekly report template
- `test_mmr_diversity.py` - MMR algorithm testing
- `../USER_ENGAGEMENT_MONITORING.md` - Complete monitoring guide

## Documentation

See `USER_ENGAGEMENT_MONITORING.md` for:
- Detailed monitoring strategy
- Alert thresholds
- Dashboard setup
- Analytics integration
- Troubleshooting guide

## Quick Test

```bash
# Test API health
curl https://ask-mirror-talk-production.up.railway.app/health

# Test MMR diversity with 3 questions
for q in "self-awareness" "leadership" "relationships"; do
  echo "Question: $q"
  curl -s -X POST https://ask-mirror-talk-production.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$q\"}" \
    | jq -r '.citations[].episode_id'
  echo ""
done
```

## Support

Questions? See:
- `DEPLOYMENT_STATUS_V2.1.0.md` - Deployment guide
- `MMR_IMPLEMENTATION_COMPLETE.md` - Technical details
- `DEPLOY_MMR_GUIDE.md` - Deployment instructions
