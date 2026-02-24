# 📊 User Engagement Monitoring Guide

**Version:** 2.1.0  
**Date:** February 18, 2026  
**Purpose:** Monitor MMR episode diversity impact on user engagement

---

## Overview

This guide helps you track how the MMR algorithm affects:
- **Episode Discovery:** Are users finding more episodes?
- **Engagement:** Are users clicking citations more?
- **Satisfaction:** Are answers still relevant and helpful?
- **Diversity:** Is the algorithm working as expected?

---

## 1. Railway Logs Monitoring

### Real-Time Log Analysis

**Watch MMR Selection Process:**
```bash
# View live logs with MMR filtering
railway logs --tail | grep "MMR:"

# Example output:
# MMR: Selected most relevant - Episode 5 (similarity: 0.845)
# MMR: Selected diverse - Episode 95 (similarity: 0.782, MMR score: 0.650)
# MMR: Final selection - 6 unique episodes from 28 candidates
```

**Track Episode Distribution:**
```bash
# Count which episodes are being selected
railway logs | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq -c | sort -rn | head -20

# Expected: No single episode dominates
# Good: Each episode appears < 30% of the time
# Bad: One episode appears > 50% of the time
```

**Monitor Query Patterns:**
```bash
# See what questions users are asking
railway logs | grep "POST /ask" | tail -20

# Track query frequency
railway logs | grep "POST /ask" | wc -l
```

### Daily Log Analysis Script

Save this as `scripts/analyze_daily_logs.sh`:

```bash
#!/bin/bash
# Daily Railway Log Analysis
# Run: bash scripts/analyze_daily_logs.sh

echo "📊 Daily Ask Mirror Talk - Engagement Report"
echo "==========================================="
echo "Date: $(date)"
echo ""

# Total queries today
TOTAL_QUERIES=$(railway logs --since 24h | grep "POST /ask" | wc -l)
echo "Total Queries (24h): $TOTAL_QUERIES"
echo ""

# Episode diversity
echo "Episode Selection Distribution:"
railway logs --since 24h | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq -c | sort -rn | head -10
echo ""

# Average candidates used
echo "MMR Candidate Pool Usage:"
railway logs --since 24h | grep "MMR: Final selection" | tail -10
echo ""

# Error rate
ERRORS=$(railway logs --since 24h | grep "ERROR" | wc -l)
echo "Errors (24h): $ERRORS"
echo ""

# Response times (if logged)
echo "Recent Response Times:"
railway logs --since 24h | grep "Request completed" | tail -10
echo ""

echo "==========================================="
echo "✅ Analysis Complete"
```

**Usage:**
```bash
# Make executable
chmod +x scripts/analyze_daily_logs.sh

# Run daily
./scripts/analyze_daily_logs.sh

# Or set up a cron job (runs daily at 9am)
# crontab -e
# 0 9 * * * /path/to/ask-mirror-talk/scripts/analyze_daily_logs.sh >> /path/to/logs/daily_report.txt
```

---

## 2. Database Analytics

### Episode Discovery Analytics

Create `scripts/analyze_episode_engagement.py`:

```python
#!/usr/bin/env python3
"""
Analyze Episode Engagement Metrics

Tracks:
- Which episodes are being cited
- Episode discovery rate
- Diversity trends over time
- Most/least cited episodes

Run: python scripts/analyze_episode_engagement.py
"""

import sys
import os
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.storage.models import Episode, Chunk

def analyze_engagement():
    """Analyze episode engagement metrics"""
    
    print("=" * 80)
    print("📊 Episode Engagement Analysis")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db: Session = SessionLocal()()
    
    try:
        # Total episodes in database
        total_episodes = db.execute(select(func.count(Episode.id))).scalar()
        print(f"Total Episodes in Database: {total_episodes}")
        print()
        
        # Episodes with chunks (ingested)
        episodes_with_chunks = db.execute(
            select(func.count(func.distinct(Chunk.episode_id)))
        ).scalar()
        print(f"Episodes Ingested (with chunks): {episodes_with_chunks}")
        print(f"Coverage: {episodes_with_chunks / total_episodes * 100:.1f}%")
        print()
        
        # Most chunked episodes (potential over-representation)
        print("Top 10 Episodes by Chunk Count:")
        print("-" * 80)
        result = db.execute(
            select(
                Episode.id,
                Episode.title,
                func.count(Chunk.id).label('chunk_count')
            )
            .join(Chunk, Episode.id == Chunk.episode_id)
            .group_by(Episode.id, Episode.title)
            .order_by(func.count(Chunk.id).desc())
            .limit(10)
        ).all()
        
        for episode_id, title, chunk_count in result:
            print(f"  {episode_id:3d}. {title[:60]:<60} ({chunk_count} chunks)")
        print()
        
        # Episodes with fewest chunks
        print("Episodes with Fewest Chunks:")
        print("-" * 80)
        result = db.execute(
            select(
                Episode.id,
                Episode.title,
                func.count(Chunk.id).label('chunk_count')
            )
            .join(Chunk, Episode.id == Chunk.episode_id)
            .group_by(Episode.id, Episode.title)
            .order_by(func.count(Chunk.id).asc())
            .limit(10)
        ).all()
        
        for episode_id, title, chunk_count in result:
            print(f"  {episode_id:3d}. {title[:60]:<60} ({chunk_count} chunks)")
        print()
        
        # Average chunks per episode
        avg_chunks = db.execute(
            select(func.avg(func.count(Chunk.id)))
            .select_from(Chunk)
            .group_by(Chunk.episode_id)
        ).scalar()
        print(f"Average Chunks per Episode: {avg_chunks:.1f}")
        print()
        
        # Chunk distribution
        print("Chunk Count Distribution:")
        print("-" * 80)
        result = db.execute(
            text("""
                SELECT 
                    CASE 
                        WHEN chunk_count < 5 THEN '1-4 chunks'
                        WHEN chunk_count < 10 THEN '5-9 chunks'
                        WHEN chunk_count < 20 THEN '10-19 chunks'
                        WHEN chunk_count < 50 THEN '20-49 chunks'
                        ELSE '50+ chunks'
                    END as bucket,
                    COUNT(*) as episode_count
                FROM (
                    SELECT episode_id, COUNT(*) as chunk_count
                    FROM chunks
                    GROUP BY episode_id
                ) as counts
                GROUP BY bucket
                ORDER BY 
                    CASE 
                        WHEN bucket = '1-4 chunks' THEN 1
                        WHEN bucket = '5-9 chunks' THEN 2
                        WHEN bucket = '10-19 chunks' THEN 3
                        WHEN bucket = '20-49 chunks' THEN 4
                        ELSE 5
                    END
            """)
        ).all()
        
        for bucket, count in result:
            print(f"  {bucket:<15} {count:3d} episodes")
        print()
        
        print("=" * 80)
        print("✅ Analysis Complete")
        print()
        print("💡 Recommendations:")
        print("  - Episodes with many chunks may appear more often in results")
        print("  - MMR helps balance this by ensuring episode diversity")
        print("  - Monitor if high-chunk episodes still dominate after MMR")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    analyze_engagement()
```

**Usage:**
```bash
# Run weekly to track trends
python scripts/analyze_episode_engagement.py
```

---

## 3. WordPress Analytics Integration

### Track Citation Clicks

Update `wordpress/ask-mirror-talk.js` to log citation interactions:

```javascript
// Add to citation click handler
function trackCitationClick(episodeId, episodeTitle, timestamp) {
  console.log('[Analytics] Citation clicked:', {
    episode_id: episodeId,
    episode_title: episodeTitle,
    timestamp: timestamp,
    question: lastQuestion // Store this globally
  });
  
  // Send to analytics (optional)
  if (window.gtag) {
    gtag('event', 'citation_click', {
      'episode_id': episodeId,
      'episode_title': episodeTitle,
      'timestamp': timestamp
    });
  }
  
  // Or send to your own endpoint
  fetch('https://ask-mirror-talk-production.up.railway.app/analytics/citation-click', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      episode_id: episodeId,
      episode_title: episodeTitle,
      timestamp: timestamp,
      question: lastQuestion
    })
  }).catch(err => console.log('Analytics error:', err));
}
```

### Create Analytics Endpoint (Optional)

Add to `app/api/main.py`:

```python
from datetime import datetime
from pydantic import BaseModel

class CitationClick(BaseModel):
    episode_id: int
    episode_title: str
    timestamp: str
    question: str

@app.post("/analytics/citation-click")
async def track_citation_click(click: CitationClick):
    """
    Track when users click on citations.
    
    In production, you might want to:
    - Store in database
    - Send to analytics platform
    - Aggregate for reporting
    """
    logger.info(
        f"Citation clicked: Episode {click.episode_id} "
        f"for question '{click.question[:50]}...'"
    )
    
    # TODO: Store in analytics database or send to analytics service
    # For now, just log it (visible in Railway logs)
    
    return {"status": "tracked"}
```

---

## 4. Key Metrics to Track

### Weekly Metrics Dashboard

Create a spreadsheet or dashboard to track:

| Week | Total Queries | Unique Episodes Cited | Avg Citations/Query | Top Episode % | Citation Clicks | User Feedback |
|------|---------------|----------------------|---------------------|---------------|-----------------|---------------|
| 1    | 245           | 127                  | 5.8                 | 12%           | 89              | Positive      |
| 2    | 312           | 156                  | 5.9                 | 10%           | 124             | Positive      |

### Metrics Definitions

**Total Queries:**
- Count of `/ask` API calls
- Track daily, weekly, monthly trends
- Source: Railway logs

**Unique Episodes Cited:**
- Number of different episodes shown in citations
- Higher = better diversity
- Target: >100 per week (for 471 episodes)
- Source: Railway logs + MMR output

**Avg Citations/Query:**
- Average number of citations per answer
- Should be ~6 (your top_k setting)
- Source: API response

**Top Episode %:**
- Percentage of queries featuring most common episode
- Before MMR: ~83%
- After MMR: <15% (ideally <10%)
- Source: Railway logs

**Citation Clicks:**
- Number of times users click citation timestamps
- Higher = more engagement
- Source: WordPress analytics

**User Feedback:**
- Qualitative feedback from users
- Comments, emails, support tickets
- Track positive/negative trends

---

## 5. Automated Monitoring Scripts

### Weekly Report Generator

Create `scripts/weekly_engagement_report.py`:

```python
#!/usr/bin/env python3
"""
Generate Weekly Engagement Report

Analyzes:
- Query volume
- Episode diversity
- MMR performance
- User engagement trends

Run: python scripts/weekly_engagement_report.py
"""

import sys
import os
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_weekly_report():
    """Generate comprehensive weekly engagement report"""
    
    print("=" * 80)
    print("📊 WEEKLY ENGAGEMENT REPORT - Ask Mirror Talk")
    print("=" * 80)
    
    week_start = datetime.now() - timedelta(days=7)
    week_end = datetime.now()
    
    print(f"Period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    print()
    
    print("=" * 80)
    print("1. QUERY VOLUME")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'POST /ask' | wc -l")
    print("  - Enter total queries: _______")
    print("  - Compare to previous week")
    print("  - Trend: ⬆️ Increasing / ➡️ Stable / ⬇️ Decreasing")
    print()
    
    print("=" * 80)
    print("2. EPISODE DIVERSITY")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Selected' | grep -oE 'Episode [0-9]+' | sort | uniq | wc -l")
    print("  - Unique episodes cited: _______")
    print("  - Target: >100 episodes (for 471 total)")
    print("  - Percentage of catalog: _______% (= unique/471 * 100)")
    print()
    
    print("=" * 80)
    print("3. EPISODE DISTRIBUTION")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Selected' | grep -oE 'Episode [0-9]+' | sort | uniq -c | sort -rn | head -10")
    print("  - List top 10 episodes:")
    print("    1. Episode ___ : ___ times")
    print("    2. Episode ___ : ___ times")
    print("    ...")
    print("  - Check: No episode should appear >30% of total queries")
    print()
    
    print("=" * 80)
    print("4. MMR PERFORMANCE")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Final selection'")
    print("  - Review candidate pool sizes (should be ~30)")
    print("  - Check for any warnings or errors")
    print("  - Average diversity rate: _______% (unique episodes per query)")
    print()
    
    print("=" * 80)
    print("5. USER FEEDBACK")
    print("=" * 80)
    print("  Check:")
    print("  - [ ] Comments on website")
    print("  - [ ] Support emails")
    print("  - [ ] Social media mentions")
    print("  - [ ] Contact form submissions")
    print()
    print("  Sentiment:")
    print("  - Positive: _____ mentions")
    print("  - Neutral: _____ mentions")
    print("  - Negative: _____ mentions")
    print()
    print("  Common themes:")
    print("  - More episode variety: _____")
    print("  - Finding new episodes: _____")
    print("  - Citations not relevant: _____")
    print()
    
    print("=" * 80)
    print("6. RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("  Based on metrics above:")
    print()
    print("  ✅ Keep Current Settings If:")
    print("     - Unique episodes > 100/week")
    print("     - No episode dominates (>30%)")
    print("     - User feedback is positive")
    print("     - No relevance complaints")
    print()
    print("  ⚙️ Tune DIVERSITY_LAMBDA If:")
    print("     - Too repetitive → Decrease to 0.6")
    print("     - Too random → Increase to 0.8")
    print("     - Relevance complaints → Increase to 0.8-0.9")
    print()
    print("  🔍 Investigate If:")
    print("     - Query volume drops significantly")
    print("     - One episode dominates (>50%)")
    print("     - Errors in logs")
    print("     - Negative user feedback")
    print()
    
    print("=" * 80)
    print("✅ Report Template Complete")
    print()
    print("💡 Save this report and compare week-over-week trends")
    print()

if __name__ == "__main__":
    generate_weekly_report()
```

**Usage:**
```bash
# Run every Monday morning
python scripts/weekly_engagement_report.py > reports/week_$(date +%Y%m%d).txt

# Review and fill in metrics
```

---

## 6. Dashboard Setup (Optional)

### Simple Google Sheets Dashboard

**Setup:**
1. Create Google Sheet: "Ask Mirror Talk Analytics"
2. Add tabs: Weekly Metrics, Episode Distribution, User Feedback
3. Track metrics manually or via Google Sheets API

**Columns:**
- Week Start Date
- Total Queries
- Unique Episodes
- Top Episode (ID + %)
- Citation Clicks
- User Feedback Score (1-5)
- Notes

**Charts:**
- Line chart: Queries over time
- Bar chart: Unique episodes per week
- Pie chart: Top 10 episodes distribution

### Advanced: Custom Dashboard

For larger scale, consider:
- **Grafana + Prometheus:** Real-time metrics
- **Datadog:** Application performance monitoring
- **Google Analytics:** Frontend engagement
- **Custom API:** Store analytics in database

---

## 7. Alert Thresholds

### Set Up Alerts

**Critical Alerts (Immediate Action):**
```
⚠️ Error Rate > 5% of requests
⚠️ Response Time > 5 seconds
⚠️ One episode appearing in >50% of queries
⚠️ API down for >5 minutes
```

**Warning Alerts (Review Within 24h):**
```
⚡ Query volume drops >30% week-over-week
⚡ Unique episodes < 50/week
⚡ Top episode >30% of queries
⚡ Multiple negative user feedback
```

**Info Alerts (Weekly Review):**
```
ℹ️ Query volume increases >50% (capacity planning)
ℹ️ New episode patterns emerging
ℹ️ Seasonal trends detected
```

---

## 8. Testing Schedule

### Daily (Automated)
- ✅ Railway health check (`/health`)
- ✅ Monitor error logs
- ✅ Check API response times

### Weekly (Manual)
- ✅ Run weekly engagement report
- ✅ Review episode distribution
- ✅ Check user feedback channels
- ✅ Test 3-5 sample questions

### Monthly (Strategic)
- ✅ Compare month-over-month trends
- ✅ Analyze seasonal patterns
- ✅ Review DIVERSITY_LAMBDA tuning
- ✅ Plan improvements/features

---

## 9. Success Indicators

### ✅ Healthy System

**Episode Diversity:**
- 100+ unique episodes cited per week
- No single episode >20% of citations
- Even distribution across catalog

**User Engagement:**
- Citation click rate >15%
- Positive feedback mentions episode discovery
- Query volume stable or growing

**System Performance:**
- <1% error rate
- <2s average response time
- MMR completing successfully

### ⚠️ Needs Attention

**Episode Diversity:**
- <50 unique episodes per week
- One episode >40% of citations
- Same episodes appearing repeatedly

**User Engagement:**
- Citation click rate <5%
- Complaints about repetitive results
- Query volume declining

**System Performance:**
- >5% error rate
- >5s average response time
- MMR errors in logs

---

## 10. Quick Reference Commands

```bash
# Daily health check
curl https://ask-mirror-talk-production.up.railway.app/health

# View live logs
railway logs --tail

# Count queries today
railway logs --since 24h | grep "POST /ask" | wc -l

# Top episodes this week
railway logs --since 7d | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq -c | sort -rn | head -10

# Unique episodes this week
railway logs --since 7d | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq | wc -l

# Check for errors
railway logs --since 24h | grep "ERROR"

# MMR performance
railway logs --since 24h | grep "MMR: Final selection"

# Test API
curl -X POST https://ask-mirror-talk-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

---

## Summary

**Monitoring Strategy:**
1. **Daily:** Check Railway logs for errors and patterns
2. **Weekly:** Run engagement report and review metrics
3. **Monthly:** Analyze trends and plan optimizations

**Key Metrics:**
- Unique episodes cited (target: >100/week)
- Top episode percentage (target: <20%)
- User feedback sentiment (target: positive)
- Citation click rate (target: >15%)

**Tools:**
- Railway logs (real-time monitoring)
- Custom Python scripts (analytics)
- Google Sheets (dashboard)
- User feedback (qualitative data)

**Success = Episode Diversity + User Satisfaction + System Reliability**

---

**🎉 You're now set up to monitor and optimize user engagement!**

Daily Run: 
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
./scripts/analyze_daily_logs.sh

Weekly Run:
source .venv/bin/activate
python scripts/weekly_engagement_report.py > reports/week_$(date +%Y%m%d).txt 

Monthly Run:
source .venv/bin/activate
python scripts/analyze_episode_engagement.py

Note: The episode engagement script requires DATABASE_URL to be set to your production database.
If you don't have production database access locally, use Railway logs for monitoring instead.
