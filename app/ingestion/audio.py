from pathlib import Path
import logging
import httpx
import os


logger = logging.getLogger(__name__)

# Maximum audio file size (25MB - OpenAI Whisper API limit)
# Can be overridden with MAX_AUDIO_SIZE_MB environment variable
# Set to 0 or negative value for unlimited (useful for local ingestion)
MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', '25'))
MAX_AUDIO_SIZE = MAX_AUDIO_SIZE_MB * 1024 * 1024 if MAX_AUDIO_SIZE_MB > 0 else float('inf')


def download_audio(audio_url: str, dest_dir: str, filename: str) -> Path:
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / filename

    if file_path.exists():
        # Check existing file size
        file_size = file_path.stat().st_size
        if MAX_AUDIO_SIZE_MB > 0 and file_size > MAX_AUDIO_SIZE:
            logger.warning(f"Cached audio file too large: {file_size / 1024 / 1024:.2f}MB > {MAX_AUDIO_SIZE_MB}MB")
            file_path.unlink()  # Delete oversized cached file
            raise ValueError(f"Audio file too large: {file_size / 1024 / 1024:.2f}MB > {MAX_AUDIO_SIZE_MB}MB")
        logger.info(f"Using cached audio file: {file_size / 1024 / 1024:.2f}MB")
        return file_path

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MirrorTalkBot/1.0)"
    }

    with httpx.stream(
        "GET",
        audio_url,
        timeout=120.0,
        follow_redirects=True,
        headers=headers,
    ) as response:
        response.raise_for_status()
        
        # Check Content-Length header if available
        content_length = response.headers.get("content-length")
        if content_length and MAX_AUDIO_SIZE_MB > 0:
            size_mb = int(content_length) / 1024 / 1024
            if int(content_length) > MAX_AUDIO_SIZE:
                logger.warning(f"Audio file too large (from Content-Length): {size_mb:.2f}MB > {MAX_AUDIO_SIZE_MB}MB")
                raise ValueError(f"Audio file too large: {size_mb:.2f}MB > {MAX_AUDIO_SIZE_MB}MB. Episode will be skipped.")
        
        # Download with size checking
        downloaded_size = 0
        with open(file_path, "wb") as f:
            for chunk in response.iter_bytes():
                downloaded_size += len(chunk)
                # Safety check during download (only if limit is set)
                if MAX_AUDIO_SIZE_MB > 0 and downloaded_size > MAX_AUDIO_SIZE:
                    logger.warning(f"Audio download exceeded {MAX_AUDIO_SIZE_MB}MB limit, aborting")
                    f.close()
                    file_path.unlink()  # Delete partial file
                    raise ValueError(f"Audio file too large: >{downloaded_size / 1024 / 1024:.2f}MB. Episode will be skipped.")
                f.write(chunk)
        
        logger.info(f"Downloaded audio: {downloaded_size / 1024 / 1024:.2f}MB")
    
    return file_path
