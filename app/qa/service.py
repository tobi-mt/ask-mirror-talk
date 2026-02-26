import gc
import time
import logging
from sqlalchemy.orm import Session

from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map
from app.qa.smart_citations import retrieve_chunks_two_tier
from app.qa.answer import compose_answer
from app.qa.cache import get_answer_cache, normalize_question
from app.storage.repository import log_qa

logger = logging.getLogger(__name__)


def answer_question(db: Session, question: str, user_ip: str, use_smart_citations: bool = True):
    """
    Answer a user's question with intelligent episode selection.
    
    DB session lifecycle:
      Phase 1 — Retrieval (DB-heavy): session open
      Phase 2 — Answer generation (OpenAI): session CLOSED to avoid idle-in-transaction timeout
      Phase 3 — Logging: fresh session
    """
    from app.core.db import get_session_local

    start_time = time.time()
    query_embedding = embed_text(question)
    
    # Check cache for near-identical questions (normalize for better matching)
    cache = get_answer_cache()
    norm_q = normalize_question(question)
    cached_response = cache.get(norm_q, query_embedding)
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

    # ── Phase 1: DB-heavy retrieval — keep session open ──
    if use_smart_citations:
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
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                },
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
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                },
                "similarity": cit['similarity'],
                "relevance_score": cit['relevance_score'],
                "total_relevant_chunks": cit['total_relevant_chunks'],
            })
    else:
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
        citation_payloads = None

    # ── Release DB session before long OpenAI call ──
    # Neon serverless kills idle-in-transaction connections after 30s;
    # OpenAI generation routinely takes 10-25s.
    db.close()

    # ── Phase 2: Answer generation (OpenAI) — no DB needed ──
    response = compose_answer(question, chunk_payloads,
                              citation_override=citation_payloads if use_smart_citations else None)

    # ── Phase 3: Log with a fresh DB session ──
    latency_ms = int((time.time() - start_time) * 1000)
    SessionLocal = get_session_local()
    log_db = SessionLocal()
    try:
        qa_log = log_qa(
            log_db,
            question=question,
            answer=response["answer"],
            episode_ids=[c["episode_id"] for c in response["citations"]],
            latency_ms=latency_ms,
            user_ip=user_ip,
        )
        qa_log_id = qa_log.id
    except Exception as e:
        logger.error("Failed to log QA: %s", e)
        qa_log_id = None
    finally:
        log_db.close()

    # Cache this response for future similar questions
    result = {
        "question": question,
        "answer": response["answer"],
        "citations": response["citations"],
        "follow_up_questions": response.get("follow_up_questions", []),
        "latency_ms": latency_ms,
        "qa_log_id": qa_log_id,
    }
    
    cache.put(norm_q, query_embedding, result)

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
    
    DB session is used only for retrieval and logging — released before
    the long-running OpenAI streaming to prevent idle-in-transaction timeouts.
    """
    import json
    from app.core.db import get_session_local

    start_time = time.time()

    # ── Immediately tell the client we're working ──
    yield f"data: {json.dumps({'type': 'status', 'message': 'Searching episodes…'})}\n\n"

    query_embedding = embed_text(question)

    # Check cache first (normalize for better matching)
    cache = get_answer_cache()
    norm_q = normalize_question(question)
    cached_response = cache.get(norm_q, query_embedding)
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

    # ── Phase 1: DB-heavy work (retrieval) — keep session open ──
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

    # ── Release the original DB session before the long streaming phase ──
    # This prevents Neon's idle-in-transaction timeout from killing the connection.
    db.close()

    # ── Phase 2: OpenAI streaming — no DB needed ──
    yield f"data: {json.dumps({'type': 'status', 'message': 'Generating answer…'})}\n\n"

    from app.qa.answer import generate_intelligent_answer_stream, _generate_basic_answer
    from app.core.config import settings

    full_answer = ""
    ranked = sorted(chunk_payloads, key=lambda c: c.get("similarity", 0), reverse=True)
    if settings.answer_generation_provider == "openai":
        try:
            for text_chunk in generate_intelligent_answer_stream(question, ranked[:6]):
                full_answer += text_chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"
        except Exception as e:
            logger.error("Streaming answer generation failed: %s", e, exc_info=True)
            full_answer = _generate_basic_answer(question, ranked[:5])
            yield f"data: {json.dumps({'type': 'chunk', 'text': full_answer})}\n\n"
    else:
        full_answer = _generate_basic_answer(question, ranked[:5])
        yield f"data: {json.dumps({'type': 'chunk', 'text': full_answer})}\n\n"

    # ── Send citations immediately — no extra latency ──
    from app.qa.answer import _build_citations, _generate_follow_up_questions
    citations = _build_citations(citation_payloads if citation_payloads else chunk_payloads)
    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

    # ── Generate follow-ups (fast, async-safe) ──
    # This is a lightweight OpenAI call; we send it as its own event so
    # the client can render citations while follow-ups load.
    try:
        follow_ups = _generate_follow_up_questions(question, full_answer, citation_payloads or chunk_payloads)
    except Exception as e:
        logger.warning("Follow-up generation failed in stream: %s", e)
        follow_ups = []
    yield f"data: {json.dumps({'type': 'follow_up', 'questions': follow_ups})}\n\n"

    # ── Phase 3: Log result with a fresh DB session ──
    latency_ms = int((time.time() - start_time) * 1000)
    SessionLocal = get_session_local()
    log_db = SessionLocal()
    qa_log_id = None
    try:
        qa_log = log_qa(
            log_db,
            question=question,
            answer=full_answer,
            episode_ids=[c["episode_id"] for c in citations],
            latency_ms=latency_ms,
            user_ip=user_ip,
        )
        qa_log_id = qa_log.id
    except Exception as e:
        logger.error("Failed to log QA: %s", e)
    finally:
        log_db.close()

    yield f"data: {json.dumps({'type': 'done', 'qa_log_id': qa_log_id, 'latency_ms': latency_ms})}\n\n"

    # Cache for next time (normalized question for better hit rate)
    cache.put(norm_q, query_embedding, {
        "question": question,
        "answer": full_answer,
        "citations": citations,
        "follow_up_questions": follow_ups,
        "latency_ms": latency_ms,
        "qa_log_id": qa_log_id,
    })

    gc.collect()
