# Railway Plan Recommendation for Ask Mirror Talk

## Current Situation Analysis

### Your Project Requirements

**API Service (`mirror-talk-api`):**
- Lightweight FastAPI server
- PostgreSQL queries + pgvector search
- OpenAI API calls for QA
- **Memory needed:** ~150-300MB
- **Usage:** 24/7 uptime needed

**Ingestion Service (`mirror-talk-ingestion`):**
- Heavy transcription workload (Whisper model)
- Audio processing with FFmpeg/PyAV
- Embedding generation (sentence-transformers)
- Database bulk inserts
- **Memory needed:** 500MB-1.5GB depending on Whisper model
- **Usage:** Periodic batch jobs (not 24/7)

### Current Problems You're Experiencing

1. ✅ **API Service:** Should work on Trial/Hobby with lightweight Dockerfile (~200MB)
2. ❌ **Ingestion Service:** Crashing with OOM errors and `ModuleNotFoundError`
3. ❌ **Memory limits:** Whisper `base` model (800MB) exceeds Trial plan limits
4. ⚠️ **Build issues:** Dockerfile.worker was incomplete (now fixed)

---

## Railway Plan Comparison

| Feature | Trial (Free) | Hobby ($5/mo) | Pro ($20/mo) |
|---------|--------------|---------------|--------------|
| **Monthly Spend** | $5 free credit | $5 base + usage | $20 base + usage |
| **RAM per Service** | 512MB | 512MB | 8GB |
| **CPU per Service** | Shared | Shared | 8 vCPU |
| **Execution Time** | Limited | No limit | No limit |
| **Build Minutes** | Limited | Unlimited | Unlimited |
| **Network Egress** | 100GB | 100GB | Included |
| **Number of Services** | Unlimited | Unlimited | Unlimited |
| **Priority Support** | ❌ | ❌ | ✅ |
| **Team Collaboration** | ❌ | ❌ | ✅ |

### Important Notes:
- **Trial**: $5 credit per month, then services pause
- **Hobby**: $5 base fee + usage (compute, memory, etc.)
- **Pro**: $20 base fee + usage, but higher resource limits

---

## Recommendation Based on Your Needs

### 🎯 **STAY ON TRIAL** (if possible) or **UPGRADE TO HOBBY ($5/mo)**

Here's why:

### Option 1: Optimize for Trial Plan (FREE - $5 credit)

**What you need to do:**
1. ✅ Use `WHISPER_MODEL=tiny` (300MB RAM vs 800MB for base)
2. ✅ Use lightweight `Dockerfile` for API (~200MB)
3. ✅ Use `Dockerfile.worker` for ingestion (already fixed)
4. ✅ Run ingestion in **batches** (10-20 episodes at a time)
5. ✅ Configure ingestion as a **manual job** (not 24/7 service)

**Expected costs within $5 credit:**
- API service: ~$2-3/month (512MB, 24/7)
- Ingestion service: ~$1-2/month (runs periodically)
- **Total: ~$3-5/month** (within free credit)

**Pros:**
✅ Completely free  
✅ Sufficient for your use case  
✅ API runs 24/7  
✅ Ingestion works in batches

**Cons:**
❌ Slower transcription (tiny model)  
❌ Must run ingestion in smaller batches  
❌ 512MB RAM limit per service

---

### Option 2: Upgrade to Hobby Plan ($5/mo base fee)

**When to choose this:**
- You exceed the $5 trial credit consistently
- You need more predictable billing
- You want unlimited build minutes

**Expected total costs:**
- Base fee: $5/month
- Usage: $2-4/month
- **Total: ~$7-9/month**

**Same optimizations as Trial:**
- Use `WHISPER_MODEL=tiny`
- Batch processing for ingestion
- Lightweight API Dockerfile

**Pros:**
✅ No service pausing when credit runs out  
✅ Unlimited build minutes  
✅ More predictable billing

**Cons:**
❌ $5 base fee (vs free with Trial)  
❌ Still limited to 512MB RAM per service

---

### Option 3: Upgrade to Pro Plan ($20/mo base fee)

**When to choose this:**
⚠️ **NOT RECOMMENDED** for your current needs

**Why NOT Pro:**
- **Overkill:** You don't need 8GB RAM or 8 vCPU
- **Cost:** $20 base + usage = ~$25-30/month
- **Your workload:** API is lightweight, ingestion is periodic
- **Better alternative:** Use Hobby plan + optimize with `tiny` Whisper model

**Only upgrade to Pro if:**
- You need `small` or `medium` Whisper models (2GB+ RAM)
- You're processing 100+ episodes daily
- You need sub-second API response times
- You have team members collaborating

---

## 💰 Cost Breakdown for Your Project

### Trial Plan (Recommended)
```
API Service (24/7):
- Memory: 512MB
- Cost: ~$2.50/month

Ingestion Service (periodic):
- Memory: 512MB (with WHISPER_MODEL=tiny)
- Runtime: ~10-15 hours/month
- Cost: ~$1.50/month

Total: ~$4/month (within $5 free credit)
```

### Hobby Plan (If Trial credit exceeded)
```
Base fee: $5/month
API Service: ~$2.50/month
Ingestion Service: ~$1.50/month

Total: ~$9/month
```

### Pro Plan (Not recommended)
```
Base fee: $20/month
API Service: ~$3/month (still lightweight)
Ingestion Service: ~$2/month (faster with base model)

Total: ~$25/month (overkill for your needs)
```

---

## 🎯 Final Recommendation

### **Start with Trial Plan + Optimizations**

**Immediate Actions:**
1. ✅ Fix Dockerfile.worker (already done)
2. ✅ Set `WHISPER_MODEL=tiny` in Railway Dashboard
3. ✅ Clear API service Start Command (use default from Dockerfile)
4. ✅ Configure ingestion service with `Dockerfile.worker`
5. ✅ Run ingestion in batches (10-20 episodes)

**Expected Result:**
- API runs 24/7 on Trial plan
- Ingestion completes successfully
- Total cost: $3-5/month (FREE within credit)

### **Upgrade to Hobby ($5/mo) if:**
- You consistently exceed $5 credit
- You want unlimited build minutes
- You need more predictable billing

### **DON'T Upgrade to Pro unless:**
- You're processing 500+ episodes/month
- You need better transcription quality (base/small model)
- You have a team collaborating on the project
- You're getting significant traffic (1000+ API calls/day)

---

## Key Optimizations to Stay on Trial/Hobby

### 1. Use Tiny Whisper Model
```bash
# Railway Dashboard > mirror-talk-ingestion > Variables
WHISPER_MODEL=tiny
```
- Reduces RAM from 800MB to 300MB
- 90-95% accuracy (good enough for QA)
- 2-3x faster transcription

### 2. Separate Dockerfiles
- ✅ `Dockerfile` (API) - 200MB, lightweight
- ✅ `Dockerfile.worker` (Ingestion) - 1.5GB, all deps

### 3. Batch Ingestion
```bash
# Process 10-20 episodes at a time
python scripts/bulk_ingest.py --max-episodes 20 --no-confirm
```

### 4. Run Ingestion as Manual Job
- Don't keep ingestion service running 24/7
- Deploy when needed, let it complete, then stop

### 5. Monitor Usage
```bash
# Railway Dashboard > Usage tab
# Watch memory, compute, and costs
```

---

## Alternative: Render.com

If Railway costs become an issue, consider **Render.com**:
- **Starter Plan:** $7/month, 512MB RAM
- **Standard Plan:** $25/month, 2GB RAM
- Simpler pricing, no base fee on Starter

But Railway is better for Docker-based deploys and Neon integration.

---

## Summary Table

| Scenario | Plan | Monthly Cost | Recommendation |
|----------|------|--------------|----------------|
| Current setup (optimized) | Trial | $0 (within $5 credit) | ✅ **Best choice** |
| Exceeded $5 credit | Hobby | ~$9 | ✅ Acceptable |
| Need better transcription | Pro | ~$25 | ⚠️ Consider upgrading Whisper model locally instead |
| High traffic API | Pro | ~$30 | ✅ Only if needed |

---

## Conclusion

### ✅ **Recommendation: Stay on Trial Plan (FREE)**

**Why:**
1. Your API is lightweight (200MB)
2. Ingestion can use `tiny` Whisper model (300MB)
3. Both services fit in 512MB RAM limit
4. Periodic ingestion keeps costs low
5. Total cost: ~$3-5/month (FREE within Trial credit)

**Upgrade to Hobby ($5/mo) only when:**
- You consistently exceed $5 credit
- You want peace of mind (no service pausing)

**Don't upgrade to Pro ($20/mo) unless:**
- You're processing 100+ episodes/week
- You need team collaboration
- You're getting 1000+ API requests/day

---

## Next Steps

1. ✅ **Apply optimizations** (tiny model, correct Dockerfiles)
2. ✅ **Test on Trial plan** for 1-2 weeks
3. 📊 **Monitor usage** in Railway Dashboard
4. 💰 **Decide on Hobby upgrade** only if needed

**You should be able to run this project completely FREE on Railway's Trial plan with the optimizations in place.** 🎉
