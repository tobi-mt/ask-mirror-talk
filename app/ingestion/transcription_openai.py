"""
OpenAI Whisper API-based transcription.
Uses OpenAI's hosted Whisper model instead of running locally.
Cost: ~$0.006 per minute of audio (~$0.24 for a 40-min episode)

IMPORTANT: OpenAI Whisper API has a 25MB file size limit.
Files larger than 25MB will be automatically compressed using FFmpeg.
"""
import os
import logging
import subprocess
import tempfile
from pathlib import Path


logger = logging.getLogger(__name__)

# OpenAI Whisper API file size limit (25MB)
OPENAI_MAX_SIZE_MB = 25
OPENAI_MAX_SIZE = OPENAI_MAX_SIZE_MB * 1024 * 1024

# Enable compression for local ingestion (safer memory usage with subprocess)
ENABLE_COMPRESSION = os.getenv('ENABLE_AUDIO_COMPRESSION', 'true').lower() == 'true'


def check_ffmpeg_installed():
    """Check if FFmpeg is installed and raise an error if not."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
    except FileNotFoundError:
        logger.error("FFmpeg is not installed!")
        logger.error("Install FFmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        logger.error("See FFMPEG_INSTALL_REQUIRED.md for detailed instructions")
        raise RuntimeError(
            "FFmpeg is not installed. Install it with: brew install ffmpeg (macOS) "
            "or apt-get install ffmpeg (Linux). See FFMPEG_INSTALL_REQUIRED.md for details."
        )
    except Exception as e:
        logger.warning(f"Could not verify FFmpeg installation: {e}")


def convert_to_mp3(input_path: Path, output_path: Path) -> None:
    """
    Convert audio file to MP3 format using FFmpeg.
    
    Args:
        input_path: Path to input audio file (any format)
        output_path: Path to save converted MP3 file
        
    Raises:
        RuntimeError: If FFmpeg fails or is not installed
    """
    logger.info(f"� Converting audio to MP3 format...")
    check_ffmpeg_installed()
    
    # Convert to MP3 with reasonable quality
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-acodec", "libmp3lame",
        "-y",  # Overwrite
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            timeout=180,  # 3 minutes max
            check=True,
            capture_output=True,
            text=True
        )
        converted_size = output_path.stat().st_size
        original_size = input_path.stat().st_size
        logger.info(
            f"✅ Conversion complete: {original_size / 1024 / 1024:.2f}MB → "
            f"{converted_size / 1024 / 1024:.2f}MB"
        )
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out after 3 minutes")
        raise RuntimeError("Audio conversion timed out")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e.stderr}")
        raise RuntimeError(f"Audio conversion failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise


def compress_audio_ffmpeg(input_path: Path, output_path: Path, target_bitrate: str = "64k") -> None:
    """
    Compress audio using FFmpeg subprocess (memory-efficient streaming).
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save compressed audio
        target_bitrate: Target bitrate (e.g., "64k", "48k", "32k")
        
    Raises:
        RuntimeError: If FFmpeg fails, times out, or is not installed
    """
    logger.info(f"🔧 Compressing audio with FFmpeg (bitrate={target_bitrate})...")
    check_ffmpeg_installed()
    
    # FFmpeg command for efficient compression:
    # -i: input file
    # -ac 1: mono audio (reduces size)
    # -ar 16000: 16kHz sample rate (sufficient for speech)
    # -b:a: target bitrate
    # -y: overwrite output
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-ac", "1",  # Mono
        "-ar", "16000",  # 16kHz
        "-b:a", target_bitrate,
        "-acodec", "libmp3lame",  # Ensure MP3 format
        "-y",  # Overwrite
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            timeout=180,  # 3 minutes max
            check=True,
            capture_output=True,
            text=True
        )
        compressed_size = output_path.stat().st_size
        original_size = input_path.stat().st_size
        logger.info(
            f"✅ Compression complete: {original_size / 1024 / 1024:.2f}MB → "
            f"{compressed_size / 1024 / 1024:.2f}MB "
            f"({100 * compressed_size / original_size:.1f}% of original)"
        )
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg compression timed out after 3 minutes")
        raise RuntimeError("Audio compression timed out")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg compression failed: {e.stderr}")
        raise RuntimeError(f"Audio compression failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error during compression: {e}")
        raise


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
    
    # Step 1: Ensure the audio is in a compatible format (convert to MP3 if needed)
    # This handles cases where the downloaded file has wrong extension or format
    original_audio_path = audio_path
    converted_audio = None
    
    # Check if file needs format conversion
    # We'll always convert to ensure compatibility with OpenAI
    try:
        converted_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        converted_path = Path(converted_audio.name)
        converted_audio.close()
        
        logger.info("🔄 Converting audio to compatible format...")
        convert_to_mp3(audio_path, converted_path)
        audio_path = converted_path
        logger.info("✅ Audio converted to MP3 format")
    except Exception as e:
        logger.error(f"Failed to convert audio format: {e}")
        if converted_audio and converted_path.exists():
            converted_path.unlink()
        raise RuntimeError(f"Audio format conversion failed: {e}")
    
    # Step 2: Check file size and compress if needed
    file_size = audio_path.stat().st_size
    file_size_mb = file_size / 1024 / 1024
    
    logger.info(f"Audio file size: {file_size_mb:.2f}MB")
    
    # Determine which file to transcribe
    transcribe_path = audio_path
    temp_compressed = None
    
    if file_size > OPENAI_MAX_SIZE:
        # File is too large for OpenAI - try compression
        if not ENABLE_COMPRESSION:
            logger.warning(
                f"Audio file too large: {file_size_mb:.2f}MB > {OPENAI_MAX_SIZE_MB}MB limit. "
                "Compression is disabled. Skipping episode."
            )
            raise ValueError(
                f"Audio file too large: {file_size_mb:.2f}MB > {OPENAI_MAX_SIZE_MB}MB. "
                "Episode skipped (compression disabled)."
            )
        
        # Try compression with progressively lower bitrates
        logger.warning(f"⚠️  Audio file is {file_size_mb:.2f}MB (limit: {OPENAI_MAX_SIZE_MB}MB)")
        logger.info("🔧 Attempting compression...")
        
        # Create temporary file for compressed audio
        temp_compressed = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = Path(temp_compressed.name)
        temp_compressed.close()
        
        try:
            # Try 64k first (good quality for speech)
            compress_audio_ffmpeg(audio_path, temp_path, target_bitrate="64k")
            compressed_size = temp_path.stat().st_size
            
            # If still too large, try lower bitrate
            if compressed_size > OPENAI_MAX_SIZE:
                logger.warning(f"Still too large ({compressed_size / 1024 / 1024:.2f}MB), trying 48k bitrate...")
                compress_audio_ffmpeg(audio_path, temp_path, target_bitrate="48k")
                compressed_size = temp_path.stat().st_size
                
                # If STILL too large, try 32k (minimum acceptable for speech)
                if compressed_size > OPENAI_MAX_SIZE:
                    logger.warning(f"Still too large ({compressed_size / 1024 / 1024:.2f}MB), trying 32k bitrate...")
                    compress_audio_ffmpeg(audio_path, temp_path, target_bitrate="32k")
                    compressed_size = temp_path.stat().st_size
                    
                    if compressed_size > OPENAI_MAX_SIZE:
                        # Even 32k isn't enough - file is just too long
                        logger.error(
                            f"Unable to compress below {OPENAI_MAX_SIZE_MB}MB even at 32k bitrate. "
                            f"Final size: {compressed_size / 1024 / 1024:.2f}MB"
                        )
                        raise ValueError(
                            f"Audio file too long to compress below {OPENAI_MAX_SIZE_MB}MB limit"
                        )
            
            logger.info(f"✅ Compressed to {compressed_size / 1024 / 1024:.2f}MB, proceeding with transcription")
            transcribe_path = temp_path
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise
    else:
        logger.info(f"✅ File size OK ({file_size_mb:.2f}MB < {OPENAI_MAX_SIZE_MB}MB limit)")

    
    try:
        # Open and transcribe the audio file (original or compressed)
        with open(transcribe_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
    except Exception as e:
        logger.error(f"OpenAI transcription failed: {e}")
        raise
    finally:
        # Clean up temporary compressed file if it was created
        if temp_compressed and transcribe_path.exists() and transcribe_path != original_audio_path:
            try:
                transcribe_path.unlink()
                logger.debug("Cleaned up temporary compressed file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file: {cleanup_error}")
        
        # Clean up temporary converted file if it was created
        if converted_audio and audio_path.exists() and audio_path != original_audio_path:
            try:
                audio_path.unlink()
                logger.debug("Cleaned up temporary converted file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up converted file: {cleanup_error}")
    
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
