from datetime import timedelta
import re


def _format_timestamp(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _select_sentences(text: str, max_sentences: int = 2) -> list[str]:
    sentences = _split_sentences(text)
    return sentences[:max_sentences]


def _make_quote(text: str, max_len: int = 160) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def compose_answer(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "answer": "I could not find anything in the Mirror Talk episodes that directly addresses that. Try rephrasing your question or sharing more context.",
            "citations": [],
        }

    # Sort by similarity if present
    ranked = sorted(chunks, key=lambda c: c.get("similarity", 0), reverse=True)

    # Extract sentences to keep answers strictly grounded in the episodes
    used_sentences = set()
    response_points = []
    for chunk in ranked[:4]:
        selected = []
        for sentence in _select_sentences(chunk["text"], max_sentences=2):
            if sentence not in used_sentences:
                used_sentences.add(sentence)
                selected.append(sentence)
        if selected:
            response_points.append(" ".join(selected))

    if not response_points:
        return {
            "answer": "I found relevant sections, but couldn't extract a clean response. Try rephrasing your question or adding more detail.",
            "citations": [],
        }

    intro = "Here are grounded reflections from Mirror Talk that speak to your question:"
    answer_lines = [intro, ""]
    for idx, point in enumerate(response_points, start=1):
        answer_lines.append(f"{idx}. {point}")

    # Optional short quote from the top chunk
    quote_text = _make_quote(ranked[0]["text"].strip())
    if quote_text:
        answer_lines.extend(["", f"In their words: \"{quote_text}\""])

    citations = []
    for chunk in ranked:
        episode = chunk["episode"]
        start_seconds = int(chunk["start_time"])
        end_seconds = int(chunk["end_time"])
        start = _format_timestamp(start_seconds)
        end = _format_timestamp(end_seconds)
        
        # Get audio URL from episode and add timestamp parameter
        audio_url = episode.get("audio_url", "")
        episode_url = audio_url
        
        # Add timestamp to URL if audio_url exists
        if audio_url:
            # For most podcast players, add #t=start_time
            episode_url = f"{audio_url}#t={start_seconds}"
        
        citations.append(
            {
                "episode_id": episode["id"],
                "episode_title": episode["title"],
                "timestamp_start": start,
                "timestamp_end": end,
                "timestamp_start_seconds": start_seconds,
                "timestamp_end_seconds": end_seconds,
                "audio_url": audio_url,
                "episode_url": episode_url,
            }
        )

    return {"answer": "\n".join(answer_lines), "citations": citations}
