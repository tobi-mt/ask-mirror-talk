# 🎙️ Mirror Talk: Your Complete Setup Guide

## Your RSS Feed
```
https://anchor.fm/s/261b1464/podcast/rss
```
✅ **Feed verified and working!**
- Podcast: Mirror Talk: Soulful Conversations
- Host: Tobi Ojekunle
- Topics: Personal growth, spirituality, well-being
- Latest episode: Financial Alignment with Julie Murphy

---

## 🚀 Quick Start (Easiest Way)

### One Command Setup
```bash
./scripts/setup_mirror_talk.sh
```

This will:
1. Configure your RSS feed automatically
2. Let you choose how many episodes to process
3. Start ingestion
4. Launch your API service
5. Verify everything works

**Time**: 15-50 minutes depending on your choice

---

## 📋 Manual Setup (If You Prefer)

### Step 1: Configure RSS Feed
```bash
# Add to your .env file
echo 'RSS_URL=https://anchor.fm/s/261b1464/podcast/rss' >> .env

# Or export it
export RSS_URL='https://anchor.fm/s/261b1464/podcast/rss'
```

### Step 2: Start Services
```bash
# Start database
docker-compose -f docker-compose.prod.yml up -d db

# Wait a moment for it to be ready
sleep 5
```

### Step 3: Run Ingestion

#### Quick Test (5 episodes, ~15-25 min)
```bash
docker-compose -f docker-compose.prod.yml run --rm app \
  python scripts/bulk_ingest.py --max-episodes 5
```

#### Standard (10 episodes, ~30-50 min)
```bash
docker-compose -f docker-compose.prod.yml run --rm app \
  python scripts/bulk_ingest.py --max-episodes 10
```

#### Full Archive (all episodes, 1-3 hours)
```bash
docker-compose -f docker-compose.prod.yml run --rm app \
  python scripts/bulk_ingest.py
```

### Step 4: Start API Service
```bash
docker-compose -f docker-compose.prod.yml up -d app
```

### Step 5: Test It!
```bash
# Check status
curl http://localhost:8000/status | jq

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What topics does Mirror Talk cover?"}' | jq
```

---

## 🔍 Expected Results

### After Processing 5 Episodes
```json
{
  "status": "ok",
  "episodes": 5,
  "chunks": 60,
  "ready": true
}
```

### Sample Question Response
```bash
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Tell me about financial wellness"}' | jq
```

Expected response:
```json
{
  "question": "Tell me about financial wellness",
  "answer": "Based on Mirror Talk episodes, financial wellness involves aligning your wealth with your inner truth and values. Julie Murphy discusses the PACT Method...",
  "citations": [
    {
      "id": 1,
      "title": "Financial Alignment Over Success: Julie Murphy on...",
      "start_time": 120.5,
      "end_time": 180.2
    }
  ],
  "latency_ms": 250
}
```

---

## 📊 Your Podcast Stats

Based on your feed, here's what to expect:

- **Podcast Title**: Mirror Talk: Soulful Conversations
- **Topic**: Personal growth, spirituality, well-being
- **Episode Length**: ~40 minutes average
- **Processing Time**: ~3-5 minutes per episode with optimizations

### Episode Examples Seen in Feed:
1. "Financial Alignment Over Success: Julie Murphy on Emotional Wellness, Money Mindset, and the PACT Method"

Your content is perfect for the Ask Mirror Talk service! Questions about:
- Personal growth strategies
- Spiritual insights
- Emotional wellness
- Financial alignment
- Self-discovery
- Mindfulness practices

---

## 🎛️ Recommended Configuration

For your podcast specifically, I recommend:

```bash
# In .env file
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
EMBEDDING_PROVIDER=sentence_transformers  # Better for spiritual/personal growth content
WHISPER_MODEL=base                        # Good balance of speed and accuracy
MAX_EPISODES_PER_RUN=10                   # Good for regular updates
TOP_K=6                                   # Retrieve 6 relevant segments
MIN_SIMILARITY=0.15                       # Not too strict, allows related topics
```

This configuration will give you:
- ✅ Accurate transcription of spiritual/wellness terminology
- ✅ Good semantic understanding for abstract concepts
- ✅ Reasonable processing time
- ✅ Quality answers to philosophical questions

---

## 🔄 Set Up Automatic Updates

### Once Initial Ingestion is Done:

```bash
# Start the worker for automatic updates
docker-compose -f docker-compose.prod.yml up -d worker

# It will check for new episodes every hour
# and automatically ingest them!
```

---

## 🧪 Test Questions for Your Podcast

Try these to test your service:

```bash
# Question 1: Broad topic
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is the PACT method?"}'

# Question 2: Specific concept
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "How does money relate to spirituality?"}'

# Question 3: General
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What topics does Mirror Talk explore?"}'
```

---

## 📈 Monitor Your Progress

### Watch Live Ingestion
```bash
docker-compose -f docker-compose.prod.yml logs -f app

# You'll see:
# [1/10] Processing episode: Financial Alignment Over Success...
#   ├─ Downloaded audio: episode_1.mp3
#   ├─ Transcribing (model=base)...
#   ├─ Transcription complete (45 segments)
#   ├─ Created 12 chunks
#   ├─ Embedding 12 chunks (batch mode)...
#   └─ ✓ Episode complete (id=1)
```

### Check Admin Dashboard
```
http://localhost:8000/admin
Username: admin
Password: (from your ADMIN_PASSWORD in .env)
```

---

## 🎉 Success Checklist

- [ ] RSS feed configured: `https://anchor.fm/s/261b1464/podcast/rss`
- [ ] Database running: `docker-compose ps`
- [ ] Ingestion completed: Check logs
- [ ] API service running: `curl http://localhost:8000/health`
- [ ] Chunks created: `curl http://localhost:8000/status | jq '.chunks'`
- [ ] Test question works: Returns answer with citations
- [ ] Worker running for auto-updates (optional)

---

## 🆘 Quick Troubleshooting

### No chunks created?
```bash
# Check if episodes were processed
docker-compose exec db psql -U mirror -d mirror_talk \
  -c "SELECT id, title FROM episodes LIMIT 5;"
```

### Service not responding?
```bash
# Check if services are running
docker-compose -f docker-compose.prod.yml ps

# Restart if needed
docker-compose -f docker-compose.prod.yml restart app
```

### Want to re-ingest?
```bash
# Clear database and start fresh
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d db
sleep 5
docker-compose -f docker-compose.prod.yml run --rm app \
  python scripts/bulk_ingest.py --max-episodes 5
```

---

## 🎯 Next Steps

1. **Run the setup**: `./scripts/setup_mirror_talk.sh`
2. **Wait for completion**: 15-50 minutes depending on your choice
3. **Test your API**: Use the curl commands above
4. **Integrate with your website**: Use the `/ask` endpoint
5. **Enable auto-updates**: Start the worker service

---

## 💡 Pro Tips for Mirror Talk Content

Your podcast covers deep, philosophical topics. Here are tips for best results:

1. **Use `sentence_transformers` embeddings** - Better for abstract concepts
2. **Set `TOP_K=6`** - Get more context for complex topics
3. **Ask open-ended questions** - "What is the PACT method?" works better than "Is PACT good?"
4. **Reference guests** - "What did Julie Murphy say about money mindset?"

---

## 📞 You're Ready!

Run this now:
```bash
./scripts/setup_mirror_talk.sh
```

Your "Ask Mirror Talk" service will be live in about 15-25 minutes! 🚀

Questions about personal growth, spirituality, and well-being from your podcast episodes will be answered automatically with citations back to the specific episodes.
