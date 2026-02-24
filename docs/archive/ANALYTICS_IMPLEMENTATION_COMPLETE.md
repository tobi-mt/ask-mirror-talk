# 📊 Analytics & User Engagement Implementation - COMPLETE

**Date:** February 20, 2026  
**Status:** ✅ Phase 1 Analytics Foundation - 100% Complete

---

## 🎯 What Was Implemented

### 1. Citation Click Tracking ✅

**Database Model:** `CitationClick`
```python
class CitationClick(Base):
    id: int
    qa_log_id: int          # Which Q&A session
    episode_id: int         # Which episode they clicked
    clicked_at: datetime    # When they clicked
    user_ip: str           # Who clicked
    timestamp: float       # Specific timestamp in episode (optional)
```

**API Endpoint:**
```
POST /api/citation/click
{
    "qa_log_id": 123,
    "episode_id": 45,
    "timestamp": 120.5  // Optional: specific timestamp in episode
}
```

**Purpose:** Track which cited episodes users actually click/listen to, enabling:
- Click-through rate (CTR) analysis
- Episode usefulness scoring
- Correlation between citation position and clicks
- A/B testing of citation strategies

---

### 2. User Feedback System ✅

**Database Model:** `UserFeedback`
```python
class UserFeedback(Base):
    id: int
    qa_log_id: int         # Which answer
    feedback_type: str     # 'positive', 'negative', 'neutral'
    rating: int           # 1-5 stars (optional)
    comment: str          # Optional user comment
    created_at: datetime
    user_ip: str
```

**API Endpoint:**
```
POST /api/feedback
{
    "qa_log_id": 123,
    "feedback_type": "positive",  // or 'negative', 'neutral'
    "rating": 5,                  // Optional: 1-5 stars
    "comment": "Great answer!"    // Optional
}
```

**Purpose:** Measure answer quality from user perspective:
- Identify poorly performing answers
- Correlate feedback with citation diversity
- Track improvement over time
- Trigger alerts for negative feedback spikes

---

### 3. Analytics API Endpoints ✅

#### **GET /api/analytics/summary?days=7**

Returns comprehensive analytics summary:
```json
{
    "period_days": 7,
    "total_questions": 150,
    "unique_users": 45,
    "avg_latency_ms": 1234.56,
    "citation_ctr_percent": 23.5,
    "top_questions": [
        {"question": "How to overcome fear?", "count": 12}
    ],
    "most_cited_episodes": [
        {"id": 45, "title": "Episode Title", "citations": 28}
    ]
}
```

**Use Cases:**
- Daily/weekly monitoring
- Performance dashboards
- Automated alerts
- Trend analysis

---

#### **GET /api/analytics/episodes**

Returns detailed episode-level analytics:
```json
{
    "episodes": [
        {
            "id": 45,
            "title": "Episode Title",
            "published_at": "2024-01-15T10:00:00",
            "citations": 28,
            "clicks": 15,
            "ctr_percent": 53.57
        }
    ]
}
```

**Use Cases:**
- Identify high-performing episodes
- Find episodes with low CTR (cited but not clicked)
- Optimize citation selection
- Content recommendations

---

### 4. Enhanced Admin Dashboard ✅

**Location:** `/admin`

**New Features:**
- 📊 **Summary Stats Card:** Questions, users, avg latency (7 days)
- 🔥 **Top Cited Episodes:** Most referenced episodes with citation counts
- 🎨 **Modern UI:** Beautiful card-based design with proper styling
- 🔗 **API Links:** Direct access to analytics APIs

**Access:**
- Same authentication as before (basic auth + IP allowlist)
- Now shows actionable insights at a glance
- Links to JSON APIs for programmatic access

---

### 5. SQL Analytics Queries ✅

**Script:** `scripts/analytics_queries.py`

**Available Queries:**
```bash
# Full summary report
python scripts/analytics_queries.py --all

# Specific analyses
python scripts/analytics_queries.py --questions      # Most common questions
python scripts/analytics_queries.py --episodes       # Most cited episodes
python scripts/analytics_queries.py --trends         # Daily usage trends
python scripts/analytics_queries.py --users          # User behavior
python scripts/analytics_queries.py --diversity      # Citation diversity
python scripts/analytics_queries.py --latency        # Response time distribution
python scripts/analytics_queries.py --hourly         # Hourly usage patterns

# Custom time period
python scripts/analytics_queries.py --all --days 30  # Last 30 days
```

**Analyses Included:**
1. **Most Common Questions** - Identify popular topics
2. **Most Cited Episodes** - Find valuable content
3. **Daily Usage Trends** - Track growth over time
4. **User Behavior Patterns** - Understand engagement
5. **Episode Diversity** - Verify MMR is working
6. **Response Time Distribution** - Monitor performance
7. **Hourly Usage Patterns** - Optimize for peak times

---

## 🚀 Deployment Steps

### Step 1: Run Database Migration

```bash
# Add new tables to database
python scripts/migrate_add_analytics_tables.py
```

This creates:
- `citation_clicks` table
- `user_feedback` table

---

### Step 2: Deploy Updated Code

```bash
# Commit and push changes
git add .
git commit -m "Add analytics infrastructure: click tracking, feedback, analytics APIs"
git push origin main

# Railway will automatically deploy
```

---

### Step 3: Verify Deployment

```bash
# Check that new endpoints work
curl https://your-app.railway.app/api/analytics/summary?days=7

# Verify admin dashboard
open https://your-app.railway.app/admin
```

---

### Step 4: Integrate Frontend Tracking

Add to your frontend (WordPress widget):

```javascript
// Track citation clicks
function trackCitationClick(qaLogId, episodeId, timestamp) {
    fetch('https://your-app.railway.app/api/citation/click', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            qa_log_id: qaLogId,
            episode_id: episodeId,
            timestamp: timestamp  // optional
        })
    });
}

// Track user feedback
function submitFeedback(qaLogId, feedbackType, rating, comment) {
    fetch('https://your-app.railway.app/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            qa_log_id: qaLogId,
            feedback_type: feedbackType,  // 'positive', 'negative', 'neutral'
            rating: rating,                // 1-5 (optional)
            comment: comment               // optional
        })
    });
}

// Example: Add click tracking to episode citations
document.querySelectorAll('.episode-citation').forEach(link => {
    link.addEventListener('click', (e) => {
        const qaLogId = link.dataset.qaLogId;
        const episodeId = link.dataset.episodeId;
        const timestamp = link.dataset.timestamp;
        trackCitationClick(qaLogId, episodeId, timestamp);
    });
});

// Example: Add feedback buttons
document.getElementById('thumbs-up').addEventListener('click', () => {
    const qaLogId = getCurrentQALogId();
    submitFeedback(qaLogId, 'positive', 5);
});

document.getElementById('thumbs-down').addEventListener('click', () => {
    const qaLogId = getCurrentQALogId();
    submitFeedback(qaLogId, 'negative', 1);
});
```

**Note:** The `/ask` endpoint response now includes `qa_log_id` so you can track it:

```javascript
// When asking a question
const response = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: userQuestion})
});

const data = await response.json();
const qaLogId = data.qa_log_id;  // Store this for later tracking

// Save qaLogId in DOM for click tracking
document.querySelector('.answer-container').dataset.qaLogId = qaLogId;
```

---

## 📈 What You Can Now Track

### Before This Implementation ✓
- ✅ Questions asked
- ✅ Episodes cited
- ✅ Response latencies
- ✅ User IPs

### NEW - Now Available ✓
- ✅ **Which citations users click** (click-through rate)
- ✅ **Which episodes are most useful** (high CTR)
- ✅ **User satisfaction** (thumbs up/down, ratings)
- ✅ **Answer quality trends** (positive vs negative feedback)
- ✅ **Episode performance** (citations vs clicks)
- ✅ **User engagement patterns** (hourly, daily trends)
- ✅ **Question popularity** (most asked topics)

---

## 🔍 Example Analytics Insights

### Query: Which episodes get cited but never clicked?
```sql
SELECT 
    e.id,
    e.title,
    COUNT(DISTINCT q.id) as citations,
    COALESCE(clicks.click_count, 0) as clicks
FROM episodes e
LEFT JOIN (
    SELECT id, UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as episode_id
    FROM qa_logs
) q ON q.episode_id = e.id
LEFT JOIN (
    SELECT episode_id, COUNT(*) as click_count
    FROM citation_clicks
    GROUP BY episode_id
) clicks ON clicks.episode_id = e.id
WHERE EXISTS (
    SELECT 1 FROM (
        SELECT UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as eid
        FROM qa_logs
    ) sub WHERE sub.eid = e.id
)
GROUP BY e.id, e.title, clicks.click_count
HAVING COUNT(DISTINCT q.id) > 5 AND COALESCE(clicks.click_count, 0) = 0
ORDER BY citations DESC;
```

**Interpretation:** These episodes are being recommended but users don't find them relevant. Consider:
- Adjusting similarity thresholds
- Improving episode metadata
- Re-evaluating citation logic

---

### Query: Correlation between citation position and CTR
```sql
-- Requires storing citation position in CitationClick model (future enhancement)
-- For now, analyze if first episode in list gets more clicks
```

---

### Query: Best performing time to answer questions
```sql
SELECT 
    EXTRACT(HOUR FROM created_at) as hour_utc,
    COUNT(*) as questions,
    AVG(latency_ms) as avg_latency,
    -- Join with feedback to get satisfaction rate
    COALESCE(
        SUM(CASE WHEN f.feedback_type = 'positive' THEN 1 ELSE 0 END)::float / 
        NULLIF(COUNT(f.id), 0) * 100,
        0
    ) as positive_rate
FROM qa_logs q
LEFT JOIN user_feedback f ON f.qa_log_id = q.id
WHERE q.created_at >= NOW() - INTERVAL '30 days'
GROUP BY hour_utc
ORDER BY hour_utc;
```

---

## 🎯 Next Steps - Phase 2

Now that Phase 1 (Analytics Foundation) is complete, you can move to:

### A/B Testing Framework
- Test different `diversity_lambda` values (0.5 vs 0.7 vs 0.9)
- Test different `max_cited_episodes` (3 vs 5 vs 7)
- Measure CTR and user satisfaction for each variant
- Automatically select best-performing configuration

### Automated Optimization
- Monitor CTR trends
- Automatically adjust parameters if CTR drops
- Alert on negative feedback spikes
- Weekly automated reports via email

### Advanced Analytics
- Cohort analysis (user retention)
- Funnel analysis (question → citation → click → listen)
- Predictive modeling (which episodes will perform best)
- Recommendation quality scoring

---

## 📊 Files Changed

### New Files
- ✅ `scripts/analytics_queries.py` - SQL analytics queries
- ✅ `scripts/migrate_add_analytics_tables.py` - Database migration
- ✅ `ANALYTICS_IMPLEMENTATION_COMPLETE.md` - This document

### Modified Files
- ✅ `app/storage/models.py` - Added CitationClick, UserFeedback models
- ✅ `app/storage/repository.py` - Added logging functions
- ✅ `app/api/main.py` - Added analytics endpoints, enhanced admin dashboard

### Ready for Frontend Integration
- WordPress widget needs to call new tracking endpoints
- Simple JavaScript additions (see examples above)
- No breaking changes to existing functionality

---

## ✅ Summary

**Phase 1 Analytics Foundation: COMPLETE (100%)**

You now have:
1. ✅ Full citation click tracking
2. ✅ User feedback system
3. ✅ Comprehensive analytics APIs
4. ✅ Beautiful admin dashboard
5. ✅ Ready-to-use SQL analytics queries
6. ✅ Database migration scripts

**The missing 30% from before is now implemented!**

**Next:** 
1. Run migration to add tables
2. Deploy to production
3. Add frontend tracking code
4. Start collecting data
5. Analyze insights to improve the system

---

## 🔗 Quick Reference

```bash
# Run database migration
python scripts/migrate_add_analytics_tables.py

# Generate analytics report
python scripts/analytics_queries.py --all

# Test analytics API
curl https://your-app.railway.app/api/analytics/summary?days=7

# View admin dashboard
open https://your-app.railway.app/admin
```

**API Endpoints:**
- `POST /api/citation/click` - Track clicks
- `POST /api/feedback` - Submit feedback
- `GET /api/analytics/summary?days=N` - Get summary
- `GET /api/analytics/episodes` - Get episode stats
- `GET /admin` - Admin dashboard (requires auth)

---

🎉 **Analytics infrastructure is now production-ready!**
