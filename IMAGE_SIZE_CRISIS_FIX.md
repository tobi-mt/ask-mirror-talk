# Image Size Crisis Fix - 8.8GB → Under 1GB

## The Problem
Railway build failed with:
```
Image of size 8.8 GB exceeded limit of 4.0 GB
```

### Root Cause
Installing `faster-whisper` and `sentence-transformers` pulls in the entire **PyTorch ecosystem**:
- PyTorch: ~4GB
- CUDA libs: ~2GB  
- Transformers models: ~1GB
- Other ML deps: ~1-2GB
- **Total: ~8.8GB**

Railway's limit: **4GB** ❌

## Solution: Remove Heavy ML Dependencies

### Strategy
Use **OpenAI APIs** instead of local models:
1. ❌ Remove `faster-whisper` → ✅ Use OpenAI Whisper API
2. ❌ Remove `sentence-transformers` → ✅ Use fallback hashed embeddings (already implemented)

### Benefits
- Image size: **8.8GB → ~800MB** 
- Build time: **5+ min → ~2 min**
- Memory usage: **2GB+ → ~300-500MB**
- Cost: Small OpenAI API usage vs Railway Pro upgrade

## Changes Made to Dockerfile.worker

### Before (8.8GB):
```dockerfile
RUN pip install --no-cache-dir \
    faster-whisper==1.0.3 \
    sentence-transformers>=2.6.0
```

### After (~800MB):
```dockerfile
RUN pip install --no-cache-dir \
    openai>=1.0.0
# Removed faster-whisper and sentence-transformers
```

## Code Changes Needed

### 1. Update Transcription to Use OpenAI Whisper API

The code needs to support OpenAI's Whisper API. I'll create a new implementation.

Create: `app/ingestion/transcription_openai.py`

```python
import os
from pathlib import Path
import openai

def transcribe_audio_openai(audio_path: Path) -> dict:
    """
    Transcribe audio using OpenAI Whisper API.
    Cost: ~$0.006 per minute of audio
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    segments = []
    texts = []
    
    for segment in transcript.segments:
        segments.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
        })
        texts.append(segment.text.strip())
    
    return {
        "language": transcript.language,
        "segments": segments,
        "raw_text": " ".join(texts).strip(),
    }
```

### 2. Update `app/ingestion/transcription.py`

```python
from pathlib import Path
import os

# Singleton for caching the Whisper model
_whisper_models = {}


def _get_whisper_model(model_name: str):
    """Lazy load and cache the Whisper model."""
    if model_name not in _whisper_models:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Use TRANSCRIPTION_PROVIDER=openai instead."
            ) from exc
        _whisper_models[model_name] = WhisperModel(model_name, device="cpu", compute_type="int8")
    return _whisper_models[model_name]


def transcribe_audio(audio_path: Path, provider: str, model_name: str):
    # Use OpenAI Whisper API if provider is "openai"
    if provider == "openai":
        from .transcription_openai import transcribe_audio_openai
        return transcribe_audio_openai(audio_path)
    
    # Original faster-whisper implementation
    if provider != "faster_whisper":
        raise ValueError(f"Unsupported transcription provider: {provider}")

    model = _get_whisper_model(model_name)
    segments, info = model.transcribe(str(audio_path), beam_size=5)

    all_segments = []
    texts = []
    for segment in segments:
        all_segments.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
            }
        )
        texts.append(segment.text.strip())

    return {
        "language": info.language,
        "segments": all_segments,
        "raw_text": " ".join(texts).strip(),
    }
```

### 3. Update `app/core/config.py`

Add transcription provider setting:

```python
class Settings(BaseSettings):
    # ...existing settings...
    
    # Transcription settings
    transcription_provider: str = "openai"  # "openai" | "faster_whisper"
    whisper_model: str = "tiny"  # Only used if faster_whisper
    
    # ...rest of settings...
```

## Railway Configuration

### Environment Variables to Set

Go to Railway Dashboard → **mirror-talk-ingestion** → **Variables**:

```
TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=sk-...your-key...
EMBEDDING_PROVIDER=local
```

### Cost Estimate

**OpenAI Whisper API Pricing:**
- $0.006 per minute of audio
- Average podcast episode: 40 minutes
- Cost per episode: 40 × $0.006 = **$0.24**
- 470 episodes: 470 × $0.24 = **$112.80 one-time**
- New episodes: ~$0.24 each

**vs Railway Pro Plan:**
- Pro Plan: $20/month × 12 = **$240/year**
- Just for larger images

**OpenAI is cheaper!**

## Alternative: Keep Local Models, Use Railway Pro

If you prefer local transcription:

### Option A: Railway Pro Plan
- $20/month base fee
- 8GB RAM limit
- No image size limit
- Can use `faster-whisper` with `base` or `small` model

### Option B: Run Ingestion Locally
- Use your Mac for transcription (has RAM)
- Only deploy API to Railway
- Manual process but free

## Implementation Plan

### Immediate Fix (Recommended):

1. ✅ Updated `Dockerfile.worker` (removed ML deps)
2. ⏳ Create `app/ingestion/transcription_openai.py` (new file)
3. ⏳ Update `app/ingestion/transcription.py` (support OpenAI)
4. ⏳ Update `app/core/config.py` (add transcription_provider)
5. ⏳ Set Railway env vars (TRANSCRIPTION_PROVIDER=openai)
6. ⏳ Redeploy and test

Would you like me to create these code changes now?

## Expected Results

### Image Size
- **Before:** 8.8GB ❌
- **After:** ~800MB ✅

### Build Time
- **Before:** 5-7 minutes (timeout)
- **After:** 2-3 minutes ✅

### Memory Usage
- **Before:** 2GB+ (OOM errors)
- **After:** 300-500MB ✅

### Cost
- **OpenAI Whisper:** ~$113 one-time + $0.24/new episode
- **Railway Trial:** FREE (stays under $5/month)
- **Total:** ~$113 one-time vs $240/year for Pro

## Status

✅ Dockerfile.worker updated (removed heavy deps)  
⏳ Code changes needed (OpenAI Whisper integration)  
⏳ Railway env vars to set  
⏳ Ready to deploy after code updates

---

**Recommendation:** Use OpenAI Whisper API - it's cheaper and simpler than upgrading to Railway Pro!
