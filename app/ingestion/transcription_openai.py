"""
OpenAI Whisper API-based transcription.
Uses OpenAI's hosted Whisper model instead of running locally.
Cost: ~$0.006 per minute of audio (~$0.24 for a 40-min episode)
"""
import os
from pathlib import Path


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
    
    # Open and transcribe the audio file
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    # Format segments to match faster-whisper format
    segments = []
    texts = []
    
    for segment in transcript.segments:
        segments.append({
            "start": float(segment["start"]),
            "end": float(segment["end"]),
            "text": segment["text"].strip(),
        })
        texts.append(segment["text"].strip())
    
    return {
        "language": transcript.language,
        "segments": segments,
        "raw_text": " ".join(texts).strip(),
    }
