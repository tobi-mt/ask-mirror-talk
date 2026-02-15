from datetime import timedelta
import re
import os
import logging

logger = logging.getLogger(__name__)


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
    """
    Generate an intelligent answer using OpenAI GPT based on relevant chunks.
    Falls back to basic extraction if OpenAI is not available.
    """
    from app.core.config import settings
    
    if not chunks:
        return {
            "answer": "I could not find anything in the Mirror Talk episodes that directly addresses that. Try rephrasing your question or sharing more context.",
            "citations": [],
        }

    # Sort by similarity if present
    ranked = sorted(chunks, key=lambda c: c.get("similarity", 0), reverse=True)

    # Try OpenAI-powered answer generation first if enabled
    if settings.answer_generation_provider == "openai":
        try:
            answer_text = _generate_intelligent_answer(question, ranked[:5])
        except Exception as e:
            logger.warning(f"OpenAI answer generation failed, falling back to basic extraction: {e}")
            answer_text = _generate_basic_answer(question, ranked[:4])
    else:
        # Use basic extraction if OpenAI is not configured
        answer_text = _generate_basic_answer(question, ranked[:4])

    # Build citations
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

    return {"answer": answer_text, "citations": citations}


def _generate_intelligent_answer(question: str, chunks: list[dict]) -> str:
    """
    Use OpenAI GPT to generate a well-structured, intelligent answer.
    """
    from openai import OpenAI
    from app.core.config import settings
    
    api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = OpenAI(api_key=api_key)
    
    # Build context from chunks
    context_parts = []
    for idx, chunk in enumerate(chunks, 1):
        episode_title = chunk["episode"]["title"]
        text = chunk["text"].strip()
        context_parts.append(f"[Source {idx} - {episode_title}]\n{text}")
    
    context = "\n\n".join(context_parts)
    
    # Create a structured prompt for GPT
    system_prompt = """You are a helpful AI assistant for Mirror Talk podcast, which focuses on personal growth, emotional intelligence, and self-development.

Your task is to answer questions based ONLY on the provided podcast excerpts. Follow these guidelines:

1. **Be Direct**: Start with a clear, direct answer to the question
2. **Be Structured**: Use paragraphs, bullet points, or numbered lists for clarity
3. **Be Specific**: Reference specific insights from the episodes
4. **Be Grounded**: Only use information from the provided sources
5. **Be Conversational**: Write in a friendly, accessible tone
6. **Be Helpful**: If the sources don't fully answer the question, acknowledge what IS covered

Format your response in a clear, easy-to-read way with proper spacing and structure."""

    user_prompt = f"""Question: {question}

Podcast Excerpts:
{context}

Please provide a well-structured, intelligent answer based on these excerpts. Use proper formatting with paragraphs, bullet points, or numbered lists to make it easy to read and understand."""

    # Call OpenAI API with configured settings
    response = client.chat.completions.create(
        model=settings.answer_generation_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=settings.answer_temperature,
        max_tokens=settings.answer_max_tokens,
    )
    
    answer = response.choices[0].message.content.strip()
    logger.info(f"Generated intelligent answer using {settings.answer_generation_model} (length: {len(answer)} chars)")
    
    return answer


def _generate_basic_answer(question: str, chunks: list[dict]) -> str:
    """
    Fallback: Basic answer generation by extracting sentences.
    """
    # Extract sentences to keep answers strictly grounded in the episodes
    used_sentences = set()
    response_points = []
    for chunk in chunks:
        selected = []
        for sentence in _select_sentences(chunk["text"], max_sentences=2):
            if sentence not in used_sentences:
                used_sentences.add(sentence)
                selected.append(sentence)
        if selected:
            response_points.append(" ".join(selected))

    if not response_points:
        return "I found relevant sections, but couldn't extract a clean response. Try rephrasing your question or adding more detail."

    intro = "Here are grounded reflections from Mirror Talk that speak to your question:"
    answer_lines = [intro, ""]
    for idx, point in enumerate(response_points, start=1):
        answer_lines.append(f"{idx}. {point}")

    # Optional short quote from the top chunk
    quote_text = _make_quote(chunks[0]["text"].strip())
    if quote_text:
        answer_lines.extend(["", f"In their words: \"{quote_text}\""])

    return "\n".join(answer_lines)
