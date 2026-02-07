from pathlib import Path


def transcribe_audio(audio_path: Path, provider: str, model_name: str):
    if provider != "faster_whisper":
        raise ValueError("Unsupported transcription provider")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install optional dependency 'transcription'."
        ) from exc

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
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
