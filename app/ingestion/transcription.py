from pathlib import Path


# Singleton for caching the Whisper model
_whisper_models = {}


def _get_whisper_model(model_name: str):
    """Lazy load and cache the Whisper model."""
    if model_name not in _whisper_models:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Install optional dependency 'transcription'."
            ) from exc
        _whisper_models[model_name] = WhisperModel(model_name, device="cpu", compute_type="int8")
    return _whisper_models[model_name]


def transcribe_audio(audio_path: Path, provider: str, model_name: str):
    if provider != "faster_whisper":
        raise ValueError("Unsupported transcription provider")

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
