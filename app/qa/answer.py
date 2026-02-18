from datetime import timedelta
import re
import os
import logging

logger = logging.getLogger(__name__)


def _format_timestamp(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling edge cases."""
    if not text.strip():
        return []
    
    # Split on sentence boundaries (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Filter out very short fragments and ensure complete sentences
    complete_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Keep sentences that are at least 20 chars and end with punctuation
        if len(sentence) >= 20:
            # If doesn't end with punctuation, it might be incomplete - skip it
            if not sentence[-1] in '.!?':
                continue
            complete_sentences.append(sentence)
    
    return complete_sentences


def _select_sentences(text: str, max_sentences: int = 3) -> list[str]:
    """Select up to max_sentences complete sentences from text."""
    sentences = _split_sentences(text)
    # If no complete sentences found, return the whole text if it's reasonably long
    if not sentences and len(text.strip()) > 40:
        return [text.strip()]
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
    logger.info(f"Answer generation provider: {settings.answer_generation_provider}")
    
    if settings.answer_generation_provider == "openai":
        try:
            logger.info("Attempting intelligent answer generation with OpenAI...")
            answer_text = _generate_intelligent_answer(question, ranked[:5])
            logger.info("Successfully generated intelligent answer")
        except Exception as e:
            logger.error(f"OpenAI answer generation failed: {e}", exc_info=True)
            logger.warning("Falling back to basic extraction")
            answer_text = _generate_basic_answer(question, ranked[:4])
    else:
        # Use basic extraction if OpenAI is not configured
        logger.info("Using basic extraction (OpenAI not enabled)")
        answer_text = _generate_basic_answer(question, ranked[:4])

    # Build citations with proper timestamps for audio playback
    citations = []
    for chunk in ranked:
        episode = chunk["episode"]
        # Ensure we have valid timestamps
        start_seconds = int(chunk["start_time"]) if chunk.get("start_time") else 0
        end_seconds = int(chunk["end_time"]) if chunk.get("end_time") else start_seconds + 30
        
        start = _format_timestamp(start_seconds)
        end = _format_timestamp(end_seconds)
        
        # Get audio URL from episode
        audio_url = episode.get("audio_url", "")
        
        # Create episode URL with timestamp for direct playback
        # Most podcast players support #t=seconds format
        episode_url = f"{audio_url}#t={start_seconds}" if audio_url else ""
        
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
                "text": _make_quote(chunk["text"], max_len=200),  # Include excerpt for context
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
    
    # Create a structured prompt for GPT - More human, intelligent, and soulful
    system_prompt = """You are a warm, empathetic, and deeply insightful AI companion helping people explore the Mirror Talk podcast's wisdom on personal growth, relationships, and emotional intelligence.

**Your Essence:**
- Conversational and approachable, like a thoughtful friend sharing insights over coffee
- Deeply curious about the human experience - psychology, relationships, self-discovery
- Empathetic and non-judgmental, honoring the complexity of being human
- Natural and flowing in your language (not robotic or overly formal)
- Uses vivid analogies and relatable examples when helpful
- Acknowledges nuance - life rarely has simple black-and-white answers

**When Answering:**
1. **Start human**: Begin with a warm, direct response that shows you understand what they're asking
2. **Weave in wisdom**: Integrate relevant podcast insights naturally into your narrative (not as mechanical citations)
3. **Connect dots**: Link ideas across episodes when you notice patterns or complementary perspectives
4. **Honor emotion**: If the question touches something personal, acknowledge the emotional dimension
5. **End with depth**: Close with a reflection or insight that adds meaning beyond the facts
6. **Be yourself**: Use "I" and "you" naturally - this is a conversation, not a lecture

**Avoid:**
- Listing facts robotically or starting every response with "Based on the podcast..."
- Excessive bullet points (use only when truly clarifying complex ideas)
- Repetitive phrasing or academic tone
- Being overly cautious or hedging unnecessarily
- Treating this like information retrieval - you're helping someone discover something meaningful

**Remember:** You're helping someone understand themselves and their relationships better. Bring intelligence, but also warmth and soul. Make them feel heard, not just informed."""

    user_prompt = f"""Question: {question}

Relevant Podcast Wisdom:
{context}

Please share a thoughtful, conversational response that helps this person understand the topic better. Weave in relevant insights naturally - feel free to connect ideas across different episodes if you notice patterns. Make it feel like a conversation, not a report."""

    # Call OpenAI API with settings optimized for natural, human responses
    response = client.chat.completions.create(
        model=settings.answer_generation_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.85,  # Higher for more natural, varied, human responses
        max_tokens=900,    # Longer to allow thoughtful, complete answers
        presence_penalty=0.4,   # Reduce repetition
        frequency_penalty=0.3,  # Encourage varied vocabulary
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
