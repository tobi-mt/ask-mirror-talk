# 🎯 QUICK REFERENCE - Mirror Talk v2.0.0

## 🚀 Test Right Now (2 minutes)

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
./scripts/health_check.sh
```

---

## 📦 What's New in v2.0.0

### Backend
- ✅ Warm, empathetic AI responses (like "friend over coffee")
- ✅ Episode deduplication (no duplicate citations)
- ✅ Accurate timestamps with `#t=seconds` format
- ✅ Better error handling throughout

### Frontend
- ✅ Version tracking (console logs v2.0.0)
- ✅ Cache-busting (versioned assets)
- ✅ Improved error handling
- ✅ Better loading states

---

## 📁 Files Updated

### WordPress (upload these)
```
wordpress/astra/ask-mirror-talk-v2.php  (v2.0.0)
wordpress/astra/ask-mirror-talk.js      (v2.0.0)
wordpress/astra/ask-mirror-talk.css
```

### Backend (already deployed)
```
app/qa/answer.py          (new system prompt)
app/qa/retrieval.py       (deduplication)
app/ingestion/pipeline_optimized.py
scripts/cleanup_orphaned_data.py
```

---

## ✅ Quick Checklist

### API Health
- [ ] Run `./scripts/health_check.sh`
- [ ] All tests pass ✅
- [ ] Episodes count > 3
- [ ] Responses are warm & conversational

### WordPress
- [ ] Upload v2.0.0 files
- [ ] Add shortcode: `[ask_mirror_talk]`
- [ ] Browser console shows "Widget v2.0.0 loaded"
- [ ] Questions submit successfully

### Browser Testing
- [ ] Chrome ✅
- [ ] Safari ✅
- [ ] Firefox ✅
- [ ] Mobile (iOS/Android) ✅

---

## 🐛 Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| Health check fails | Check Railway logs: `railway logs` |
| "I could not find anything" | Only 3 episodes loaded, run ingestion |
| Widget not showing | Check functions.php has require statement |
| Old version showing | Hard refresh: Cmd+Shift+R |
| CORS error | Check ALLOWED_ORIGINS has your domain |

---

## 📚 Documentation

- **Complete Guide:** `PROJECT_COMPLETE_READY_FOR_TESTING.md`
- **Next Steps:** `NEXT_STEPS_GUIDE.md`
- **WordPress:** `WORDPRESS_TESTING_GUIDE.md`
- **UX Changes:** `UX_AI_IMPROVEMENTS_COMPLETE.md`

---

## 🎯 Success Criteria

✅ **Warm AI responses** (2-4 paragraphs, empathetic tone)  
✅ **Unique citations** (each episode once)  
✅ **Working timestamps** (clicks jump to exact moment)  
✅ **No errors** (console clean, form works)  
✅ **Cross-browser** (Chrome, Safari, Firefox, mobile)

---

## 🔑 Key Commands

```bash
# Test API
./scripts/health_check.sh

# View logs
railway logs --tail

# Local test
curl -X POST https://ask-mirror-talk-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is alignment?"}'
```

---

**Ready to test! 🚀**
