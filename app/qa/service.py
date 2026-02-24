import gc
import time
from sqlalchemy.orm import Session

from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map
from app.qa.smart_citations import retrieve_chunks_two_tier
from app.qa.answer import compose_answer
from app.qa.cache import get_answer_cache
from app.storage.repository import log_qa


def answer_question(db: Session, question: str, user_ip: str, use_smart_citations: bool = True):
    """
    Answer a user's question with intelligent episode selection.
    
    Args:
        db: Database session
        question: User's question
        user_ip: User's IP for logging
        use_smart_citations: If True, uses smart episode selection (top 5 most relevant episodes)
                            If False, uses legacy behavior (all chunks as citations)
    """
    start_time = time.time()
    query_embedding = embed_text(question)
    
    # Check cache for near-identical questions
    cache = get_answer_cache()
    cached_response = cache.get(question, query_embedding)
    if cached_response:
        latency_ms = int((time.time() - start_time) * 1000)
        # Log the cached response too
        qa_log = log_qa(
            db,
            question=question,
            answer=cached_response["answer"],
            episode_ids=[c["episode_id"] for c in cached_response.get("citations", [])],
            latency_ms=latency_ms,
            user_ip=user_ip,
        )
        cached_response["latency_ms"] = latency_ms
        cached_response["qa_log_id"] = qa_log.id
        cached_response["question"] = question
        return cached_response

    if use_smart_citations:
        # New: Two-tier retrieval for smart episode citations
        retrieval_result = retrieve_chunks_two_tier(db, query_embedding)
        answer_chunks = retrieval_result['answer_chunks']
        citation_episodes = retrieval_result['citation_episodes']
        
        # Load episode metadata for answer generation (all chunks)
        all_episode_ids = list({chunk.episode_id for chunk, _ in answer_chunks})
        episode_map = load_episode_map(db, all_episode_ids)
        
        # Prepare chunks for answer generation
        chunk_payloads = []
        for chunk, similarity in answer_chunks:
            episode = episode_map.get(chunk.episode_id)
            if not episode:
                continue
            chunk_payloads.append({
                "text": chunk.text,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                },
                "similarity": similarity,
            })
        
        # Prepare top episodes for citations
        citation_payloads = []
        for cit in citation_episodes:
            episode = episode_map.get(cit['episode_id'])
            if not episode:
                continue
            citation_payloads.append({
                "text": cit['chunk'].text,
                "start_time": cit['chunk'].start_time,
                "end_time": cit['chunk'].end_time,
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                },
                "similarity": cit['similarity'],
                "relevance_score": cit['relevance_score'],
                "total_relevant_chunks": cit['total_relevant_chunks'],
            })
        
        # Generate answer using all chunks, but return only top episode citations
        response = compose_answer(question, chunk_payloads, citation_override=citation_payloads)
        
    else:
        # Legacy: Use all retrieved chunks for both answer and citations
        retrieved = retrieve_chunks(db, query_embedding)
        episode_ids = list({chunk.episode_id for chunk, _ in retrieved})
        episode_map = load_episode_map(db, episode_ids)
        
        chunk_payloads = []
        for chunk, similarity in retrieved:
            episode = episode_map.get(chunk.episode_id)
            if not episode:
                continue
            chunk_payloads.append({
                "text": chunk.text,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                },
                "similarity": similarity,
            })
        
        response = compose_answer(question, chunk_payloads)
    
    latency_ms = int((time.time() - start_time) * 1000)

    qa_log = log_qa(
        db,
        question=question,
        answer=response["answer"],
        episode_ids=[c["episode_id"] for c in response["citations"]],
        latency_ms=latency_ms,
        user_ip=user_ip,
    )

    # Cache this response for future similar questions
    result = {
        "question": question,
        "answer": response["answer"],
        "citations": response["citations"],
        "follow_up_questions": response.get("follow_up_questions", []),
        "latency_ms": latency_ms,
        "qa_log_id": qa_log.id,
    }
    
    cache.put(question, query_embedding, result)

    # Explicit garbage collection to free up memory
    gc.collect()

    return result


def answer_question_stream(db: Session, question: str, user_ip: str):
    """
    Stream an answer using SSE. Yields JSON events:
      - {"type": "chunk", "text": "..."} for each text chunk
      - {"type": "citations", "citations": [...]} at the end
      - {"type": "follow_up", "questions": [...]} at the end
      - {"type": "done", "qa_log_id": ..., "latency_ms": ...} final event
    """
    import json

    start_time = time.time()
    query_embedding = embed_text(question)

    # Check cache first
    cache = get_answer_cache()
    cached_response = cache.get(question, query_embedding)
    if cached_response:
        latency_ms = int((time.time() - start_time) * 1000)
        qa_log = log_qa(
            db,
            question=question,
            answer=cached_response["answer"],
            episode_ids=[c["episode_id"] for c in cached_response.get("citations", [])],
            latency_ms=latency_ms,
            user_ip=user_ip,
        )
        # Stream the full cached answer as a single chunk for instant display
        yield f"data: {json.dumps({'type': 'chunk', 'text': cached_response['answer']})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'citations': cached_response.get('citations', [])})}\n\n"
        yield f"data: {json.dumps({'type': 'follow_up', 'questions': cached_response.get('follow_up_questions', [])})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'qa_log_id': qa_log.id, 'latency_ms': latency_ms, 'cached': True})}\n\n"
        return

    # Retrieve chunks
    retrieval_result = retrieve_chunks_two_tier(db, query_embedding)
    answer_chunks = retrieval_result['answer_chunks']
    citation_episodes = retrieval_result['citation_episodes']

    all_episode_ids = list({chunk.episode_id for chunk, _ in answer_chunks})
    episode_map = load_episode_map(db, all_episode_ids)

    chunk_payloads = []
    for chunk, similarity in answer_chunks:
        episode = episode_map.get(chunk.episode_id)
        if not episode:
            continue
        chunk_payloads.append({
            "text": chunk.text,
            "start_time": chunk.start_time,
            "end_time": chunk.end_time,
            "episode": {"id": episode.id, "title": episode.title, "audio_url": episode.audio_url or ""},
            "similarity": similarity,
        })

    citation_payloads = []
    for cit in citation_episodes:
        episode = episode_map.get(cit['episode_id'])
        if not episode:
            continue
        citation_payloads.append({
            "text": cit['chunk'].text,
            "start_time": cit['chunk'].start_time,
            "end_time": cit['chunk'].end_time,
            "episode": {"id": episode.id, "title": episode.title, "audio_url": episode.audio_url or ""},
            "similarity": cit['similarity'],
            "relevance_score": cit['relevance_score'],
            "total_relevant_chunks": cit['total_relevant_chunks'],
        })

    # Stream the answer text
    from app.qa.answer import generate_intelligent_answer_stream, _generate_basic_answer
    from app.core.config import settings

    full_answer = ""
    if settings.answer_generation_provider == "openai":
        try:
            ranked = sorted(chunk_payloads, key=lambda c: c.get("similarity", 0), reverse=True)
            for text_chunk in generate_intelligent_answer_stream(question, ranked[:5]):
                full_answer += text_chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Streaming failed: %s", e)
            full_answer = _generate_basic_answer(question, sorted(chunk_payloads, key=lambda c: c.get("similarity", 0), reverse=True)[:4])
            yield f"data: {json.dumps({'type': 'chunk', 'text': full_answer})}\n\n"
    else:
        full_answer = _generate_basic_answer(question, sorted(chunk_payloads, key=lambda c: c.get("similarity", 0), reverse=True)[:4])
        yield f"data: {json.dumps({'type': 'chunk', 'text': full_answer})}\n\n"

    # Build citations (reuse compose_answer's citation builder logic)
    response = compose_answer(question, chunk_payloads, citation_override=citation_payloads)
    citations = response["citations"]
    follow_ups = response.get("follow_up_questions", [])

    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
    yield f"data: {json.dumps({'type': 'follow_up', 'questions': follow_ups})}\n\n"

    latency_ms = int((time.time() - start_time) * 1000)
    qa_log = log_qa(
        db,
        question=question,
        answer=full_answer,
        episode_ids=[c["episode_id"] for c in citations],
        latency_ms=latency_ms,
        user_ip=user_ip,
    )

    # Cache for next time
    cache.put(question, query_embedding, {
        "question": question,
        "answer": full_answer,
        "citations": citations,
        "follow_up_questions": follow_ups,
        "latency_ms": latency_ms,
        "qa_log_id": qa_log.id,
    })

    yield f"data: {json.dumps({'type': 'done', 'qa_log_id': qa_log.id, 'latency_ms': latency_ms})}\n\n"

    gc.collect()
