# 🏗️ Analytics System Architecture

## 📊 Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WORDPRESS FRONTEND                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  User Interface (Widget)                                     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │ │
│  │  │ Question   │  │ Citations  │  │ Feedback   │            │ │
│  │  │ Input      │  │ Display    │  │ Buttons    │            │ │
│  │  └────────────┘  └────────────┘  └────────────┘            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              ▲                                      │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  WordPress Analytics JavaScript                              │ │
│  │  • wordpress-widget-analytics.js                             │ │
│  │  • Tracks citation clicks                                    │ │
│  │  • Handles feedback submission                               │ │
│  │  • Manages qa_log_id                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               │ HTTPS/JSON
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     RAILWAY PRODUCTION API                          │
│                  (ask-mirror-talk-production.up.railway.app)        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Endpoints                                           │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  POST /ask                                             │ │ │
│  │  │  • Processes question                                  │ │ │
│  │  │  • Returns answer + citations + qa_log_id             │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  POST /api/citation/click                             │ │ │
│  │  │  • Logs citation click event                          │ │ │
│  │  │  • Stores: qa_log_id, episode_id, timestamp           │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  POST /api/feedback                                   │ │ │
│  │  │  • Records user feedback                              │ │ │
│  │  │  • Stores: qa_log_id, feedback_type, rating           │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  GET /api/analytics/summary                           │ │ │
│  │  │  • Returns aggregated analytics                       │ │ │
│  │  │  • CTR, feedback rates, totals                        │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  GET /api/analytics/episodes                          │ │ │
│  │  │  • Returns per-episode metrics                        │ │ │
│  │  │  • Click counts, rankings                             │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  GET /admin                                           │ │ │
│  │  │  • Analytics dashboard (HTML)                         │ │ │
│  │  │  • Visual charts and tables                           │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Business Logic Layer                                        │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │ QA Service  │  │ Smart        │  │ Analytics    │       │ │
│  │  │ (service.py)│  │ Citations    │  │ Repository   │       │ │
│  │  │             │  │ (MMR Logic)  │  │ (queries)    │       │ │
│  │  └─────────────┘  └──────────────┘  └──────────────┘       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database (Railway)                               │ │
│  │                                                              │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐│ │
│  │  │ Episodes       │  │ Chunks         │  │ QALog          ││ │
│  │  │ • id           │  │ • id           │  │ • id           ││ │
│  │  │ • title        │  │ • episode_id   │  │ • question     ││ │
│  │  │ • audio_url    │  │ • text         │  │ • answer       ││ │
│  │  │ • metadata     │  │ • embedding    │  │ • created_at   ││ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘│ │
│  │                                                              │ │
│  │  ┌────────────────┐  ┌────────────────┐                    │ │
│  │  │ CitationClick  │  │ UserFeedback   │                    │ │
│  │  │ • id           │  │ • id           │  🆕 Analytics      │ │
│  │  │ • qa_log_id    │  │ • qa_log_id    │     Tables        │ │
│  │  │ • episode_id   │  │ • feedback_type│                    │ │
│  │  │ • timestamp    │  │ • rating       │                    │ │
│  │  │ • clicked_at   │  │ • created_at   │                    │ │
│  │  └────────────────┘  └────────────────┘                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: User Question to Analytics

```
1. USER ASKS QUESTION
   │
   ├─► WordPress Widget HTML
   │   └─► <form id="amt-question-form">
   │
   ├─► JavaScript Event Handler
   │   └─► askQuestion(questionText)
   │
   ▼
2. API REQUEST
   │
   ├─► POST https://ask-mirror-talk-production.up.railway.app/ask
   │   └─► Body: { "question": "What is this about?" }
   │
   ▼
3. BACKEND PROCESSING
   │
   ├─► QA Service
   │   ├─► Generate embedding for question
   │   ├─► Search Pinecone for relevant chunks
   │   ├─► Apply MMR diversity algorithm
   │   ├─► Generate answer with OpenAI
   │   └─► Log to QALog table → returns qa_log_id
   │
   ▼
4. API RESPONSE
   │
   ├─► Returns JSON:
   │   {
   │     "question": "...",
   │     "answer": "...",
   │     "citations": [...],
   │     "qa_log_id": 123  ← 🆕 For tracking
   │   }
   │
   ▼
5. FRONTEND DISPLAY
   │
   ├─► Display answer
   ├─► Render citations as clickable links
   ├─► Store qa_log_id in JavaScript variable
   ├─► Show feedback buttons
   └─► Initialize click tracking
   │
   ▼
6. USER CLICKS CITATION
   │
   ├─► Browser navigates to episode URL
   ├─► JavaScript tracks click (async, non-blocking)
   │
   ├─► POST /api/citation/click
   │   └─► Body: {
   │         "qa_log_id": 123,
   │         "episode_id": 45,
   │         "timestamp": 120.5
   │       }
   │
   ├─► Backend saves to CitationClick table
   └─► Console: "✅ Citation click tracked"
   │
   ▼
7. USER GIVES FEEDBACK (OPTIONAL)
   │
   ├─► User clicks 👍 or 👎
   │
   ├─► POST /api/feedback
   │   └─► Body: {
   │         "qa_log_id": 123,
   │         "feedback_type": "positive",
   │         "rating": 5
   │       }
   │
   ├─► Backend saves to UserFeedback table
   ├─► Show "Thank you" message
   └─► Console: "✅ Feedback submitted"
   │
   ▼
8. ANALYTICS AGGREGATION
   │
   ├─► Queries run on database:
   │   ├─► Total questions (from QALog)
   │   ├─► Total clicks (from CitationClick)
   │   ├─► Total feedback (from UserFeedback)
   │   ├─► CTR = clicks / citations shown
   │   └─► Positive rate = positive / total feedback
   │
   ├─► Available via:
   │   ├─► GET /api/analytics/summary
   │   ├─► GET /api/analytics/episodes
   │   └─► GET /admin (dashboard)
   │
   ▼
9. INSIGHTS & OPTIMIZATION
   │
   ├─► Identify top-performing episodes
   ├─► Analyze low-click episodes
   ├─► Correlate feedback with citations
   ├─► Adjust MMR parameters
   └─► Improve future recommendations
```

---

## 🎯 Citation Selection Flow (MMR Algorithm)

```
Question: "What topics does the podcast cover?"
   │
   ▼
1. EMBEDDING GENERATION
   │
   ├─► OpenAI Embeddings API
   └─► Vector: [0.123, -0.456, 0.789, ...]
   │
   ▼
2. VECTOR SEARCH (Pinecone)
   │
   ├─► Query embedding against chunk embeddings
   ├─► Returns top 20 most similar chunks
   └─► Each chunk has:
       • episode_id
       • timestamp
       • similarity score
       • text content
   │
   ▼
3. MMR DIVERSITY ALGORITHM
   │
   ├─► Parameters:
   │   • lambda = 0.7 (70% relevance, 30% diversity)
   │   • max_citations = 5
   │
   ├─► For each candidate chunk:
   │   • Relevance score (from Pinecone)
   │   • Max similarity to already-selected chunks
   │   • MMR score = λ * relevance - (1-λ) * max_similarity
   │
   ├─► Select chunk with highest MMR score
   ├─► Deduplicate by episode_id
   └─► Repeat until 5 episodes selected
   │
   ▼
4. CITATION ENRICHMENT
   │
   ├─► Look up episode metadata from database:
   │   • Episode title
   │   • Audio URL
   │   • Publication date
   │
   ├─► Format timestamps (seconds → MM:SS)
   ├─► Generate excerpt from chunk text
   └─► Build citation objects
   │
   ▼
5. RETURN TO USER
   │
   └─► Citations in response JSON
       [
         {
           "episode_id": 45,
           "episode_title": "Episode Title",
           "episode_url": "https://...",
           "timestamp_start_seconds": 120.5,
           "text": "Relevant excerpt...",
           "similarity_score": 0.87
         },
         ...
       ]
```

---

## 📊 Analytics Dashboard Data Flow

```
Admin Dashboard Request
   │
   ├─► GET /admin
   │
   ▼
Backend Queries
   │
   ├─► Query 1: Total Questions
   │   └─► SELECT COUNT(*) FROM qa_log
   │
   ├─► Query 2: Total Citation Clicks
   │   └─► SELECT COUNT(*) FROM citation_click
   │
   ├─► Query 3: Total Feedback
   │   └─► SELECT COUNT(*) FROM user_feedback
   │
   ├─► Query 4: Total Citations Shown
   │   └─► Calculate from qa_log citations field
   │
   ├─► Query 5: Episode Analytics
   │   └─► SELECT episode_id, COUNT(*) as click_count
   │       FROM citation_click
   │       GROUP BY episode_id
   │       ORDER BY click_count DESC
   │
   ├─► Query 6: Feedback Breakdown
   │   └─► SELECT feedback_type, COUNT(*)
   │       FROM user_feedback
   │       GROUP BY feedback_type
   │
   ▼
Calculations
   │
   ├─► CTR = (total_clicks / total_citations_shown) * 100
   ├─► Positive Rate = (positive_feedback / total_feedback) * 100
   └─► Average Rating = AVG(rating) FROM user_feedback
   │
   ▼
HTML Dashboard
   │
   ├─► Summary Cards:
   │   ├─► 📊 Total Questions
   │   ├─► 🖱️ Citation Clicks
   │   ├─► 💬 User Feedback
   │   ├─► 📈 CTR
   │   └─► ⭐ Positive Rate
   │
   ├─► Episode Performance Table:
   │   ├─► Episode Title
   │   ├─► Click Count
   │   └─► Rank
   │
   └─► Recent Activity Log
       └─► Last 10 actions (clicks, feedback)
```

---

## 🔐 Security & Privacy

```
┌─────────────────────────────────────────┐
│  SECURITY MEASURES                      │
├─────────────────────────────────────────┤
│                                         │
│  ✅ CORS Enabled                        │
│     • Allows WordPress domain           │
│     • Preflight requests handled        │
│                                         │
│  ✅ HTTPS Only                          │
│     • All API calls encrypted           │
│     • Railway provides SSL              │
│                                         │
│  ✅ No PII Collection                   │
│     • No user emails                    │
│     • No IP addresses                   │
│     • No session cookies                │
│                                         │
│  ✅ Anonymized Analytics                │
│     • Only qa_log_id tracked            │
│     • No user identification            │
│                                         │
│  ✅ Rate Limiting (Railway)             │
│     • DDoS protection                   │
│     • Resource quotas                   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 Scalability Architecture

```
┌─────────────────────────────────────────────────────────┐
│  CURRENT ARCHITECTURE (Production Ready)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Railway App Instance                                   │
│  ├─► FastAPI (single container)                        │
│  ├─► PostgreSQL (Railway managed)                      │
│  ├─► Pinecone (cloud vector DB)                        │
│  └─► OpenAI API (external)                             │
│                                                         │
│  Handles: ~100 requests/second                          │
│  Database: Up to 10GB data                              │
│  Vector Index: 100K+ chunks                             │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  FUTURE SCALING OPTIONS                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Horizontal Scaling                                  │
│     ├─► Multiple Railway instances                     │
│     ├─► Load balancer                                  │
│     └─► Shared PostgreSQL database                     │
│                                                         │
│  2. Caching Layer                                       │
│     ├─► Redis for frequent queries                     │
│     ├─► Cache embeddings                               │
│     └─► Cache analytics aggregations                   │
│                                                         │
│  3. CDN for Static Assets                              │
│     ├─► CloudFlare for JS/CSS                          │
│     └─► Reduce bandwidth costs                         │
│                                                         │
│  4. Async Task Queue                                    │
│     ├─► Celery for background jobs                     │
│     ├─► Batch analytics calculations                   │
│     └─► Scheduled data exports                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

```
┌────────────────────┬──────────────────────────────┐
│ Layer              │ Technology                   │
├────────────────────┼──────────────────────────────┤
│ Frontend           │ Vanilla JavaScript + CSS     │
│ Backend Framework  │ FastAPI (Python 3.11)        │
│ Database           │ PostgreSQL (Railway)         │
│ Vector DB          │ Pinecone                     │
│ LLM                │ OpenAI GPT-4                 │
│ Embeddings         │ OpenAI text-embedding-3-small│
│ Deployment         │ Railway.app                  │
│ CMS Integration    │ WordPress                    │
│ HTTP Client        │ Fetch API                    │
│ ORM                │ SQLAlchemy                   │
│ Analytics          │ Custom SQL queries           │
└────────────────────┴──────────────────────────────┘
```

---

## ✅ System Status

```
┌─────────────────────────────────────────┐
│  COMPONENT STATUS                       │
├─────────────────────────────────────────┤
│  ✅ Database          OPERATIONAL       │
│  ✅ API Endpoints     OPERATIONAL       │
│  ✅ Vector Index      OPERATIONAL       │
│  ✅ LLM Service       OPERATIONAL       │
│  ✅ Admin Dashboard   OPERATIONAL       │
│  ✅ Analytics         OPERATIONAL       │
│  ✅ CORS              CONFIGURED        │
│  ✅ Migrations        COMPLETE          │
│  ⏳ WordPress         PENDING SETUP     │
└─────────────────────────────────────────┘
```

---

**Architecture Version:** 2.0 (Analytics Edition)  
**Last Updated:** February 20, 2026  
**Status:** Production Ready ✅
