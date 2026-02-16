"""
OpenAI Whisper API-based transcription.
Uses OpenAI's hosted Whisper model instead of running locally.
Cost: ~$0.006 per minute of audio (~$0.24 for a 40-min episode)

IMPORTANT: OpenAI Whisper API has a 25MB file size limit.
Files larger than 25MB will be SKIPPED in production (compression disabled to prevent OOM crashes).
For local ingestion, set MAX_AUDIO_SIZE_MB=0 to process large files.
"""
import os
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

# OpenAI Whisper API file size limit (25MB)
# Can be overridden with MAX_AUDIO_SIZE_MB environment variable
# Set to 0 for unlimited (useful for local ingestion with powerful hardware)
MAX_FILE_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', '25'))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024 if MAX_FILE_SIZE_MB > 0 else float('inf')


def transcribe_audio_openai(audio_path: Path) -> dict:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        dict with keys: language, segments, raw_text
        
    Cost: ~$0.006 per minute of audio
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai package not installed. Run: pip install openai>=1.0.0"
        ) from exc
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Check file size - SKIP compression to avoid OOM crashes
    file_size = audio_path.stat().st_size
    
    if MAX_FILE_SIZE_MB > 0 and file_size > MAX_FILE_SIZE:
        # File too large - skip it in production (compression causes OOM crashes on Railway)
        logger.warning(
            f"Audio file too large: {file_size / 1024 / 1024:.2f}MB > {MAX_FILE_SIZE_MB}MB limit. "
            "Skipping episode (compression disabled to prevent container crashes)."
        )
        raise ValueError(
            f"Audio file too large: {file_size / 1024 / 1024:.2f}MB > {MAX_FILE_SIZE_MB}MB. "
            "Episode skipped."
        )
    
    # File is within limits (or unlimited mode) - transcribe directly
    logger.info(f"Audio file size: {file_size / 1024 / 1024:.2f}MB " + 
                (f"(within {MAX_FILE_SIZE_MB}MB limit)" if MAX_FILE_SIZE_MB > 0 else "(unlimited mode)"))

    
    try:
        # Open and transcribe the audio file
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
    except Exception as e:
        logger.error(f"OpenAI transcription failed: {e}")
        raise
    
    # Format segments to match faster-whisper format
    segments = []
    texts = []
    
    for segment in transcript.segments:
        # OpenAI returns TranscriptionSegment objects, not dicts - use attribute access
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
