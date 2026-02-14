# OpenAI Whisper API File Size Fix

## Problem
OpenAI Whisper API has a **25MB file size limit** for audio uploads. Some podcast episodes exceed this limit (e.g., 26.38MB).

## Solution
Implemented automatic audio compression when files exceed 25MB:

### Features
1. **Pre-upload Size Check**: Checks file size before sending to OpenAI
2. **Automatic Compression**: Uses FFmpeg + pydub to compress audio
3. **Multi-stage Compression**: 
   - First tries 64k bitrate (mono)
   - Falls back to 48k bitrate if still too large
   - Fails gracefully if compression isn't enough
4. **Temporary File Handling**: Cleans up compressed files automatically

### Implementation Details

**File**: `app/ingestion/transcription_openai.py`

```python
# OpenAI Whisper API file size limit (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

def compress_audio(input_path, output_path, target_bitrate="64k"):
    """Compress audio using FFmpeg via pydub"""
    from pydub import AudioSegment
    audio = AudioSegment.from_file(input_path)
    audio.export(
        output_path,
        format="mp3",
        bitrate=target_bitrate,
        parameters=["-ac", "1"]  # Convert to mono
    )
```

### Compression Strategy
- **Original**: 26.38MB stereo MP3
- **Compressed (64k mono)**: ~8-12MB (estimated)
- **Compression (48k mono)**: ~6-9MB (if needed)

### Dependencies Added
- `pydub>=0.25.1` (Python audio processing)
- FFmpeg (already in Dockerfile.worker)

### Quality Impact
- **Bitrate**: 64k mono is sufficient for speech transcription
- **Accuracy**: Whisper is trained on various quality levels
- **Original**: Preserved in storage/S3 if needed

## Testing

After deploying, run ingestion:
```bash
railway run python -m scripts.bulk_ingest
```

You should see:
```
Processing: Episode 123...
  ⚠️  Audio file is 26.38MB (limit: 25MB)
  🔧 Compressing audio...
  ✅ Compressed to 10.24MB
  ✅ Transcribed with OpenAI (en, 2850 words)
```

## Cost Impact
No additional cost - compression happens before upload, so only the compressed file is sent to OpenAI API.

## Error Handling
If an episode is too large even after compression:
```python
ValueError: Audio file too large even after compression: 27.5MB > 25MB
```

**Solution**: 
1. Manually split long episodes into parts
2. Or increase compression (lower bitrate, but may affect quality)

## Files Changed
- ✅ `app/ingestion/transcription_openai.py` - Added compression logic
- ✅ `requirements.txt` - Added pydub
- ✅ `Dockerfile.worker` - Added pydub to pip install

## Status
✅ **READY TO DEPLOY**

The ingestion service can now handle episodes >25MB automatically.
