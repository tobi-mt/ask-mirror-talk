import re


def _split_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_segments(segments: list[dict], max_chars: int, min_chars: int):
    chunks = []
    current_text = []
    current_start = None
    current_end = None

    for seg in segments:
        if current_start is None:
            current_start = seg["start"]
        current_end = seg["end"]
        current_text.append(seg["text"])

        if sum(len(t) for t in current_text) >= max_chars:
            joined = " ".join(current_text)
            chunks.extend(_finalize_chunk(joined, current_start, current_end, max_chars, min_chars))
            current_text = []
            current_start = None
            current_end = None

    if current_text:
        joined = " ".join(current_text)
        chunks.extend(_finalize_chunk(joined, current_start, current_end, max_chars, min_chars))

    return chunks


def _finalize_chunk(text: str, start: float, end: float, max_chars: int, min_chars: int):
    if len(text) <= max_chars:
        return [{"text": text, "start": start, "end": end}]

    sentences = _split_sentences(text)
    chunks = []
    buffer = []
    buf_len = 0
    chunk_start = start
    for sentence in sentences:
        buffer.append(sentence)
        buf_len += len(sentence)
        if buf_len >= min_chars:
            chunk_text = " ".join(buffer)
            chunks.append({"text": chunk_text, "start": chunk_start, "end": end})
            buffer = []
            buf_len = 0
            chunk_start = end

    if buffer:
        chunk_text = " ".join(buffer)
        chunks.append({"text": chunk_text, "start": chunk_start, "end": end})

    return chunks
