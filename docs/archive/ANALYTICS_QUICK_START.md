# ✅ Analytics Implementation - Quick Start Guide

**Date:** February 20, 2026  
**Status:** Complete & Ready to Use

---

## 🎉 What's New

### 1. Citation Click Tracking
Track when users actually click on cited episodes.

**Frontend Integration (WordPress widget):**
```javascript
// When user clicks an episode citation
fetch('https://your-app.railway.app/api/citation/click', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        qa_log_id: responseData.qa_log_id,  // From /ask response
        episode_id: episodeId,
        timestamp: 120.5  // Optional: specific time in episode
    })
});
```

### 2. User Feedback
Let users rate answers with thumbs up/down.

**Frontend Integration:**
```javascript
// Thumbs up
fetch('https://your-app.railway.app/api/feedback', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        qa_log_id: responseData.qa_log_id,
        feedback_type: 'positive',
        rating: 5  // Optional 1-5
    })
});
```

### 3. Analytics APIs
Query analytics data programmatically.

```bash
# Get 7-day summary
curl https://your-app.railway.app/api/analytics/summary?days=7

# Get episode analytics
curl https://your-app.railway.app/api/analytics/episodes
```

### 4. Enhanced Admin Dashboard
Visit: `https://your-app.railway.app/admin`

Now shows:
- 📊 Summary stats (questions, users, latency)
- 🔥 Top cited episodes
- 💬 Recent questions
- 🔄 Ingestion runs

### 5. SQL Analytics Queries
Run comprehensive analytics from command line.

```bash
# Full report
python scripts/analytics_queries.py --all

# Specific analyses
python scripts/analytics_queries.py --questions
python scripts/analytics_queries.py --episodes
python scripts/analytics_queries.py --trends
```

---

## 🚀 Deployment Steps

### ✅ Step 1: Already Done
Migration has been run locally - tables created:
- `citation_clicks`
- `user_feedback`

### 📦 Step 2: Deploy to Production

```bash
# Commit changes
git add .
git commit -m "Add analytics: click tracking, feedback, analytics APIs"
git push origin main
```

Railway will automatically:
1. Deploy new code
2. Create analytics tables (on first request)
3. Enable new API endpoints

### 🔍 Step 3: Verify Production

```bash
# Check analytics endpoint
curl https://your-app.railway.app/api/analytics/summary?days=7

# Check admin dashboard
open https://your-app.railway.app/admin
```

### 🎨 Step 4: Update Frontend (WordPress)

1. **Modify `/ask` response handling** to save `qa_log_id`:
```javascript
const response = await fetch('/ask', {
    method: 'POST',
    body: JSON.stringify({question: userQuestion})
});
const data = await response.json();
// NEW: Save for tracking
window.currentQALogId = data.qa_log_id;
```

2. **Add click tracking** to episode citations:
```javascript
document.querySelectorAll('.episode-link').forEach(link => {
    link.addEventListener('click', () => {
        fetch('/api/citation/click', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                qa_log_id: window.currentQALogId,
                episode_id: link.dataset.episodeId
            })
        });
    });
});
```

3. **Add feedback buttons**:
```html
<div class="feedback-buttons">
    <button id="thumbs-up">👍 Helpful</button>
    <button id="thumbs-down">👎 Not Helpful</button>
</div>

<script>
document.getElementById('thumbs-up').addEventListener('click', () => {
    fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            qa_log_id: window.currentQALogId,
            feedback_type: 'positive',
            rating: 5
        })
    });
});
</script>
```

---

## 📊 Sample Analytics Insights

### Last 7 Days (from actual data):

**Most Asked Questions:**
- "I'm successful, yet..." (9 times)
- "I feel disconnected..." (8 times)
- "Love" (5 times)

**Most Cited Episodes:**
1. "Surrender to Lead" - 43 citations
2. "The Joy That Comes" - 43 citations
3. "JayMikee's 2 Most POWERFUL..." - 32 citations

**Engagement:**
- 112 total questions
- 10 unique users
- Avg response time: 4.1 seconds
- 67.86% of questions cite 6 episodes (MMR is working!)

---

## 🔧 Useful Commands

```bash
# Run analytics report
python scripts/analytics_queries.py --all --days 30

# Check specific metrics
python scripts/analytics_queries.py --questions --days 7
python scripts/analytics_queries.py --episodes --days 7
python scripts/analytics_queries.py --trends --days 30

# Re-run migration (safe, idempotent)
python scripts/migrate_add_analytics_tables.py
```

---

## 📈 What You Can Now Measure

1. **Citation Click-Through Rate (CTR)**
   - Which cited episodes users actually click
   - Identify low-performing citations

2. **User Satisfaction**
   - Positive vs negative feedback ratio
   - Average rating per answer

3. **Episode Performance**
   - Citations vs clicks per episode
   - High CTR = relevant citations
   - Low CTR = cited but not useful

4. **Usage Trends**
   - Questions per day
   - Peak hours
   - User retention

5. **Answer Quality**
   - Response times
   - Feedback correlation
   - Topic coverage

---

## 🎯 Next Steps

### Immediate (After Deploy):
1. ✅ Deploy to production
2. ✅ Add frontend tracking code
3. ✅ Monitor analytics daily

### Week 1:
1. Verify click tracking is working
2. Collect baseline metrics
3. Identify any issues

### Week 2-4:
1. Analyze CTR by episode
2. Identify low-performing citations
3. Test parameter adjustments
4. Compare before/after metrics

### Future (Phase 2):
1. A/B testing framework
2. Automated optimization
3. Predictive analytics
4. Email reports

---

## 🔗 API Reference

### POST /api/citation/click
Track when user clicks a citation.

**Request:**
```json
{
    "qa_log_id": 123,
    "episode_id": 45,
    "timestamp": 120.5
}
```

### POST /api/feedback
Submit user feedback on answer.

**Request:**
```json
{
    "qa_log_id": 123,
    "feedback_type": "positive",
    "rating": 5,
    "comment": "Very helpful!"
}
```

### GET /api/analytics/summary?days=7
Get analytics summary.

**Response:**
```json
{
    "total_questions": 112,
    "unique_users": 10,
    "avg_latency_ms": 4104.20,
    "citation_ctr_percent": 23.5,
    "top_questions": [...],
    "most_cited_episodes": [...]
}
```

### GET /api/analytics/episodes
Get episode-level analytics.

**Response:**
```json
{
    "episodes": [{
        "id": 45,
        "title": "Episode Title",
        "citations": 28,
        "clicks": 15,
        "ctr_percent": 53.57
    }]
}
```

---

✅ **All 3 tasks complete! Ready to deploy and start collecting data.**
