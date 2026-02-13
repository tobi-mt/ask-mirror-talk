# Missing Dependency Fix - requests

## New Error Discovered
After fixing the import error and Docker cache, a new error appeared:
```
ModuleNotFoundError: No module named 'requests'
```

## Root Cause
`faster-whisper` depends on the `requests` library, but it wasn't included in the Dockerfile.

The error trace shows:
```python
File "/usr/local/lib/python3.11/site-packages/faster_whisper/utils.py", line 8, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
```

## Solution
Added `requests>=2.31.0` to:
1. `Dockerfile` - pip install section
2. `requirements.txt` - for reference

## Commit
- `ccbb5fa` - Added requests dependency

## Status
✅ Fix pushed to Bitbucket  
🔄 Railway is rebuilding (will take 10-15 minutes)  

## What to Expect Next

### After Railway Deploys
The ingestion should finally work! You'll see:
```
✓ Processing episode X/470
  ├─ Downloaded audio: episode_X.mp3
  ├─ Transcribing (model=base)...
  ├─ Processing audio with duration XX:XX
  ├─ Detected language 'en' with probability 0.99
  ├─ Transcription complete (XXX segments)
  └─ ✓ Episode complete
```

### Dependencies Now Complete
- ✅ FFmpeg binary
- ✅ FFmpeg dev libraries (libavcodec-dev, etc.)
- ✅ gcc and python3-dev for building
- ✅ PyAV (av>=12.0.0)
- ✅ requests>=2.31.0 ← NEW
- ✅ faster-whisper==1.0.3

## Timeline of Fixes

1. **First attempt:** Added PyAV dependencies (9d8042c)
2. **Second attempt:** Fixed import error + busted cache (877a69f)
3. **Third attempt:** Added requests dependency (ccbb5fa) ← Current

## Why This Keeps Happening
Each error reveals the next missing piece:
1. Missing PyAV → Added libavcodec-dev, av
2. Missing import → Fixed ingest_all_episodes.py
3. Missing requests → Added requests package

This is normal when dependencies weren't fully tested in Railway environment before.

## Final Check
Once deployed, test:
```bash
railway run python -c "import av, requests, faster_whisper; print('All imports OK!')"
```

Should output:
```
All imports OK!
```

Then run ingestion:
```bash
railway run bash
python scripts/bulk_ingest.py --max-episodes 5 --no-confirm
```

This should FINALLY work! 🤞

## Monitoring
```bash
railway logs --service mirror-talk-ingestion -f
```

Watch for successful transcription logs (not errors).
