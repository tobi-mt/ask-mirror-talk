"""
OpenAI Whisper API-based transcription.
Uses OpenAI's hosted Whisper model instead of running locally.
Cost: ~$0.006 per minute of audio (~$0.24 for a 40-min episode)

Handles OpenAI's 25MB file size limit by compressing audio if needed.
"""
import os
import subprocess
import tempfile
from pathlib import Path


# OpenAI Whisper API file size limit (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes


def compress_audio(input_path: Path, output_path: Path, target_bitrate: str = "64k") -> None:
    """
    Compress audio file to reduce size using FFmpeg directly (low memory, fast).
    
    Args:
        input_path: Original audio file
        output_path: Path for compressed audio
        target_bitrate: Target audio bitrate (e.g., "64k", "96k", "128k")
    """
    # Use FFmpeg directly instead of pydub to minimize memory usage
    # This streams the audio instead of loading it all into memory
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-ac", "1",  # Convert to mono
        "-ar", "16000",  # Reduce sample rate to 16kHz (good for speech)
        "-b:a", target_bitrate,  # Set bitrate
        "-y",  # Overwrite output file
        "-loglevel", "error",  # Only show errors
        str(output_path)
    ]
    
    try:
        print(f"  🔧 Running FFmpeg compression (bitrate={target_bitrate})...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 120 second timeout (increased for large files)
            check=True
        )
        print(f"  ✅ FFmpeg compression complete")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg compression failed: {e.stderr}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"FFmpeg compression timed out after 120 seconds") from None


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
    
    # Check file size and compress if needed
    file_size = audio_path.stat().st_size
    temp_file = None
    
    if file_size > MAX_FILE_SIZE:
        print(f"  ⚠️  Audio file is {file_size / 1024 / 1024:.2f}MB (limit: 25MB)")
        print(f"  🔧 Compressing audio...")
        
        # Create temporary compressed file
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        try:
            # Try 64k bitrate first (aggressive compression)
            compress_audio(audio_path, temp_path, target_bitrate="64k")
            compressed_size = temp_path.stat().st_size
            
            if compressed_size > MAX_FILE_SIZE:
                # Still too large, try even lower bitrate
                print(f"  ⚠️  First compression: {compressed_size / 1024 / 1024:.2f}MB, trying lower bitrate...")
                compress_audio(audio_path, temp_path, target_bitrate="48k")
                compressed_size = temp_path.stat().st_size
            
            if compressed_size > MAX_FILE_SIZE:
                # Give up if still too large
                os.unlink(temp_path)
                raise ValueError(
                    f"Audio file too large even after compression: {compressed_size / 1024 / 1024:.2f}MB > 25MB"
                )
            
            print(f"  ✅ Compressed to {compressed_size / 1024 / 1024:.2f}MB")
            audio_path_to_use = temp_path
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                os.unlink(temp_path)
            raise
    else:
        audio_path_to_use = audio_path
    
    try:
        # Open and transcribe the audio file
        with open(audio_path_to_use, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
    finally:
        # Clean up temporary compressed file
        if temp_file and Path(temp_file.name).exists():
            os.unlink(temp_file.name)
    
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
