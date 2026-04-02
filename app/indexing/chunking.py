import re


def _split_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _build_chunk(segments: list[dict]) -> dict:
    return {
        "text": " ".join(seg["text"].strip() for seg in segments if seg["text"].strip()).strip(),
        "start": segments[0]["start"],
        "end": segments[-1]["end"],
    }


def _chunk_from_sentences(
    sentences: list[str],
    start: float,
    end: float,
    max_chars: int,
    min_chars: int,
) -> list[dict]:
    if not sentences:
        return []

    total_duration = max(end - start, 0.0)
    sentence_lengths = [max(len(sentence), 1) for sentence in sentences]
    total_length = sum(sentence_lengths)

    chunks = []
    buffer = []
    buffer_len = 0
    consumed_length = 0

    for sentence, sentence_len in zip(sentences, sentence_lengths):
        projected_len = buffer_len + sentence_len + (1 if buffer else 0)
        if buffer and projected_len > max_chars and buffer_len >= min_chars:
            chunk_start = start + (consumed_length / total_length) * total_duration
            chunk_end = start + ((consumed_length + buffer_len) / total_length) * total_duration
            chunks.append({
                "text": " ".join(buffer),
                "start": chunk_start,
                "end": chunk_end,
            })
            consumed_length += buffer_len
            buffer = []
            buffer_len = 0

        buffer.append(sentence)
        buffer_len += sentence_len + (1 if len(buffer) > 1 else 0)

    if buffer:
        chunk_start = start + (consumed_length / total_length) * total_duration
        chunks.append({
            "text": " ".join(buffer),
            "start": chunk_start,
            "end": end,
        })

    return chunks


def _split_long_segment(segment: dict, max_chars: int, min_chars: int) -> list[dict]:
    text = segment["text"].strip()
    if len(text) <= max_chars:
        return [segment]

    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        parts = []
        start = 0
        while start < len(text):
            parts.append(text[start:start + max_chars].strip())
            start += max_chars
        sentences = [part for part in parts if part]

    return _chunk_from_sentences(sentences, segment["start"], segment["end"], max_chars, min_chars)


def _finalize_chunk(segments: list[dict], max_chars: int, min_chars: int):
    if not segments:
        return []

    chunks = []
    buffer = []
    buffer_len = 0

    for segment in segments:
        segment_text = segment["text"].strip()
        if not segment_text:
            continue

        if len(segment_text) > max_chars:
            if buffer:
                chunks.append(_build_chunk(buffer))
                buffer = []
                buffer_len = 0
            chunks.extend(_split_long_segment(segment, max_chars, min_chars))
            continue

        projected_len = buffer_len + len(segment_text) + (1 if buffer else 0)
        if buffer and projected_len > max_chars and buffer_len >= min_chars:
            chunks.append(_build_chunk(buffer))
            buffer = []
            buffer_len = 0

        buffer.append(segment)
        buffer_len += len(segment_text) + (1 if len(buffer) > 1 else 0)

    if buffer:
        chunks.append(_build_chunk(buffer))

    return chunks


def chunk_segments(segments: list[dict], max_chars: int, min_chars: int):
    chunks = []
    current_segments = []
    current_len = 0

    for seg in segments:
        seg_text = seg["text"].strip()
        if not seg_text:
            continue

        projected_len = current_len + len(seg_text) + (1 if current_segments else 0)
        current_segments.append(seg)
        current_len = projected_len

        if current_len >= max_chars:
            chunks.extend(_finalize_chunk(current_segments, max_chars, min_chars))
            current_segments = []
            current_len = 0

    if current_segments:
        chunks.extend(_finalize_chunk(current_segments, max_chars, min_chars))

    return chunks
