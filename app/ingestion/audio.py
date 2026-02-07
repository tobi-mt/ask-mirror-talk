from pathlib import Path
import httpx


def download_audio(audio_url: str, dest_dir: str, filename: str) -> Path:
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / filename

    if file_path.exists():
        return file_path

    with httpx.stream("GET", audio_url, timeout=120.0) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return file_path
