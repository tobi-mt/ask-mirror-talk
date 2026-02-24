# 🔄 WordPress to Railway API Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR WORDPRESS SITE                       │
│                 (mirrortalkpodcast.com)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User visits page with
                            │ [ask_mirror_talk] shortcode
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ASTRA THEME                             │
│                                                              │
│  📄 ask-mirror-talk.php                                     │
│     └─ Renders HTML form                                    │
│     └─ Loads JavaScript & CSS                               │
│                                                              │
│  🎨 ask-mirror-talk.css                                     │
│     └─ Styles the widget                                    │
│                                                              │
│  ⚡ ask-mirror-talk.js                                      │
│     └─ Handles form submission                              │
│     └─ Calls WordPress AJAX                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ AJAX POST with question
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     WPGETAPI PLUGIN                          │
│                                                              │
│  API ID: mirror_talk_ask                                    │
│  Endpoint: /ask                                              │
│  Method: POST                                                │
│  Base URL: https://ask-mirror-talk-production...            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST Request
                            │ {"question": "..."}
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY HOSTING                           │
│            ask-mirror-talk-production                        │
│                                                              │
│  📦 FastAPI Application                                     │
│     └─ POST /ask endpoint                                   │
│     └─ Rate limiting (20/min)                               │
│     └─ CORS validation                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SQL Queries
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEON DATABASE                             │
│                  (PostgreSQL + pgvector)                     │
│                                                              │
│  📊 Tables:                                                 │
│     • episodes (3 rows)                                     │
│     • chunks (354 rows)                                     │
│     • embeddings (vector search)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Returns matching chunks
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI PROCESSING                             │
│                                                              │
│  1. Convert question to embedding                           │
│  2. Vector similarity search                                │
│  3. Retrieve top 6 relevant chunks                          │
│  4. Generate answer from context                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ JSON Response
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      RESPONSE                                │
│                                                              │
│  {                                                          │
│    "question": "What is this about?",                       │
│    "answer": "Mirror Talk is...",                           │
│    "sources": [                                             │
│      {                                                      │
│        "episode_title": "Episode 1",                        │
│        "episode_number": 1,                                 │
│        "audio_url": "..."                                   │
│      }                                                      │
│    ],                                                       │
│    "processing_time": 1.23                                  │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Back through WPGetAPI
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     USER'S BROWSER                           │
│                                                              │
│  JavaScript displays:                                        │
│  • Answer text                                              │
│  • Episode citations                                        │
│  • Links to episodes                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

### User asks: "What topics does this podcast cover?"

**Step 1: Frontend (WordPress)**
```javascript
// ask-mirror-talk.js
fetch('/wp-admin/admin-ajax.php', {
  method: 'POST',
  body: 'action=ask_mirror_talk&question=What topics...'
})
```

**Step 2: WordPress AJAX Handler**
```php
// ask-mirror-talk.php
function ask_mirror_talk_ajax_handler() {
  $question = $_POST['question'];
  $response = wpgetapi_endpoint('mirror_talk_ask', 'mirror_talk_ask', [
    'body' => ['question' => $question]
  ]);
  wp_send_json_success($response);
}
```

**Step 3: WPGetAPI**
```
POST https://ask-mirror-talk-production.up.railway.app/ask
Content-Type: application/json

{"question": "What topics does this podcast cover?"}
```

**Step 4: Railway API**
```python
# app/api/main.py
@app.post("/ask")
def ask(payload: AskRequest, db: Session):
    response = answer_question(db, payload.question)
    return response
```

**Step 5: Database Query**
```sql
-- Vector similarity search
SELECT * FROM chunks
WHERE embedding <=> query_embedding
ORDER BY similarity DESC
LIMIT 6
```

**Step 6: Response Back**
```json
{
  "answer": "The podcast covers topics like...",
  "sources": [
    {"episode_title": "Episode 1", "episode_number": 1}
  ]
}
```

---

## Configuration Points

### 1. WPGetAPI Settings
```
Location: WordPress Admin → WPGetAPI → Setup
API Name: Mirror Talk Ask
Unique ID: mirror_talk_ask
Base URL: https://ask-mirror-talk-production.up.railway.app
Endpoint: /ask
Method: POST
```

### 2. Astra Theme Files
```
Location: /wp-content/themes/astra/
Files:
  - ask-mirror-talk.php (shortcode)
  - ask-mirror-talk.js (JavaScript)
  - ask-mirror-talk.css (styles)

Activation: functions.php
  require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
```

### 3. Railway Environment
```
URL: ask-mirror-talk-production.up.railway.app
Database: Neon PostgreSQL
ALLOWED_ORIGINS: 
  - https://mirrortalkpodcast.com
  - https://www.mirrortalkpodcast.com
```

---

## Security Flow

```
User Input → Sanitize → WordPress Nonce Check → WPGetAPI
                ↓
         Rate Limiting (Railway)
                ↓
         CORS Validation (Railway)
                ↓
         Input Validation (FastAPI)
                ↓
         Parameterized Queries (SQLAlchemy)
```

---

## Error Handling Flow

```
Error Occurs
    │
    ├─ JavaScript catches fetch error
    │  └─ Display: "We couldn't reach the service"
    │
    ├─ WordPress AJAX fails
    │  └─ Return: wp_send_json_error()
    │
    ├─ WPGetAPI fails
    │  └─ Return: is_wp_error()
    │
    ├─ Railway API error
    │  └─ Return: HTTP 500 with error message
    │
    └─ Database error
       └─ Log error, return generic message
```

---

## Performance Considerations

**Caching:**
- WordPress: WPGetAPI can cache responses (optional)
- Railway: No caching (always fresh results)
- Database: Connection pooling enabled

**Timeouts:**
- WPGetAPI: 30 seconds
- Railway: Default 30 seconds
- Database: 10 second connection timeout

**Rate Limiting:**
- Railway API: 20 requests per minute per IP
- WordPress: No limit (but proxied through server)

---

## Monitoring Points

**1. WordPress (Debug Log)**
```
/wp-content/debug.log
```

**2. Railway (Application Logs)**
```
Railway Dashboard → Service → Logs
```

**3. Database (Neon Console)**
```
Neon Dashboard → Monitoring
```

**4. Browser (Console)**
```
F12 → Console tab
```

---

## Testing Checklist

- [ ] WPGetAPI test returns valid JSON
- [ ] Shortcode renders on page
- [ ] Form submission sends AJAX request
- [ ] Railway receives POST to /ask
- [ ] Database query executes
- [ ] Response returns to browser
- [ ] Answer displays on page
- [ ] Citations render correctly
- [ ] No JavaScript errors in console
- [ ] No PHP errors in debug.log

---

This visual guide shows the complete flow from user question to answer display!
