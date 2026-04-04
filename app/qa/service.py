import gc
import time
import logging
from sqlalchemy.orm import Session

from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map
from app.qa.smart_citations import (
    retrieve_chunks_two_tier,
    select_citation_segments,
)
from app.qa.answer import compose_answer
from app.qa.cache import get_answer_cache, normalize_question
from app.storage.repository import log_qa

logger = logging.getLogger(__name__)


def _maybe_log_qa(
    db: Session,
    *,
    question: str,
    answer: str,
    episode_ids: list[int],
    latency_ms: int,
    user_ip: str,
    is_cached: bool,
    is_answered: bool,
    log_interaction: bool,
):
    if not log_interaction:
        return None
    return log_qa(
        db,
        question=question,
        answer=answer,
        episode_ids=episode_ids,
        latency_ms=latency_ms,
        user_ip=user_ip,
        is_cached=is_cached,
        is_answered=is_answered,
    )


def _log_qa_with_fresh_session(
    *,
    question: str,
    answer: str,
    episode_ids: list[int],
    latency_ms: int,
    user_ip: str,
    is_cached: bool,
    is_answered: bool,
    log_interaction: bool,
    context: str,
):
    if not log_interaction:
        return None

    from app.core.db import get_session_local, safe_close_session

    SessionLocal = get_session_local()
    log_db = SessionLocal()
    try:
        qa_log = _maybe_log_qa(
            log_db,
            question=question,
            answer=answer,
            episode_ids=episode_ids,
            latency_ms=latency_ms,
            user_ip=user_ip,
            is_cached=is_cached,
            is_answered=is_answered,
            log_interaction=log_interaction,
        )
        return qa_log.id if qa_log else None
    except Exception as exc:
        logger.error("Failed to log QA during %s: %s", context, exc, exc_info=True)
        return None
    finally:
        safe_close_session(log_db, context=context)


def _select_citations_with_fresh_session(
    *,
    question: str,
    answer_text: str,
    candidate_episodes: list[dict],
    context: str,
):
    if not candidate_episodes:
        return []

    from app.core.db import get_session_local, safe_close_session

    SessionLocal = get_session_local()
    refine_db = SessionLocal()
    try:
        refined = select_citation_segments(
            refine_db,
            question=question,
            answer_text=answer_text,
            candidate_episodes=candidate_episodes,
        )
        return refined or []
    except Exception as exc:
        logger.error("Failed to select citation segments during %s: %s", context, exc, exc_info=True)
        return []
    finally:
        safe_close_session(refine_db, context=context)


def answer_question(
    db: Session,
    question: str,
    user_ip: str,
    use_smart_citations: bool = True,
    log_interaction: bool = True,
    bypass_cache: bool = False,
):
    """
    Answer a user's question with intelligent episode selection.
    
    DB session lifecycle:
      Phase 1 — Retrieval (DB-heavy): session open
      Phase 2 — Answer generation (OpenAI): session CLOSED to avoid idle-in-transaction timeout
      Phase 3 — Logging: fresh session
    """
    from app.core.db import get_session_local, safe_close_session

    start_time = time.time()
    cache = get_answer_cache()
    norm_q = normalize_question(question)
    if not bypass_cache:
        exact_cached_response = cache.get_exact(norm_q)
        if exact_cached_response:
            latency_ms = int((time.time() - start_time) * 1000)
            exact_citations = exact_cached_response.get("citations", [])
            qa_log_id = _log_qa_with_fresh_session(
                question=question,
                answer=exact_cached_response["answer"],
                episode_ids=[c["episode_id"] for c in exact_citations],
                latency_ms=latency_ms,
                user_ip=user_ip,
                is_cached=True,
                is_answered=len(exact_citations) > 0,
                log_interaction=log_interaction,
                context="qa_exact_cache_logging",
            )
            exact_cached_response["latency_ms"] = latency_ms
            exact_cached_response["qa_log_id"] = qa_log_id
            exact_cached_response["question"] = question
            return exact_cached_response

    query_embedding = embed_text(question)

    if not bypass_cache:
        # Check cache for near-identical questions (normalize for better matching)
        cached_response = cache.get(norm_q, query_embedding)
        if cached_response:
            latency_ms = int((time.time() - start_time) * 1000)
            # Log the cached response too
            cached_citations = cached_response.get("citations", [])
            qa_log_id = _log_qa_with_fresh_session(
                question=question,
                answer=cached_response["answer"],
                episode_ids=[c["episode_id"] for c in cached_citations],
                latency_ms=latency_ms,
                user_ip=user_ip,
                is_cached=True,
                is_answered=len(cached_citations) > 0,
                log_interaction=log_interaction,
                context="qa_similarity_cache_logging",
            )
            cached_response["latency_ms"] = latency_ms
            cached_response["qa_log_id"] = qa_log_id
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
                    "published_year": episode.published_at.year if episode.published_at else None,
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
    safe_close_session(db, context="qa_retrieval_phase")

    # ── Phase 2: Answer generation (OpenAI) — no DB needed ──
    response = compose_answer(question, chunk_payloads,
                              citation_override=citation_payloads if use_smart_citations else None)

    if use_smart_citations and citation_payloads:
        refined_citation_chunks = _select_citations_with_fresh_session(
            question=question,
            answer_text=response["answer"],
            candidate_episodes=citation_payloads,
            context="qa_citation_segment_selection",
        )
        if refined_citation_chunks:
            from app.qa.answer import _build_citations
            response["citations"] = _build_citations(refined_citation_chunks)
        else:
            response["citations"] = []

    # ── Phase 3: Log with a fresh DB session ──
    latency_ms = int((time.time() - start_time) * 1000)
    qa_log_id = _log_qa_with_fresh_session(
        question=question,
        answer=response["answer"],
        episode_ids=[c["episode_id"] for c in response["citations"]],
        latency_ms=latency_ms,
        user_ip=user_ip,
        is_cached=False,
        is_answered=len(response["citations"]) > 0,
        log_interaction=log_interaction,
        context="qa_logging_phase",
    )

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


def answer_question_stream(
    db: Session,
    question: str,
    user_ip: str,
    context: list[dict] | None = None,
    log_interaction: bool = True,
    bypass_cache: bool = False,
):
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
    from app.core.db import get_session_local, safe_close_session

    start_time = time.time()

    # ── Immediately tell the client we're working ──
    yield f"data: {json.dumps({'type': 'status', 'message': 'Searching episodes…'})}\n\n"

    # Check cache first (normalize for better matching)
    cache = get_answer_cache()
    norm_q = normalize_question(question)
    exact_cached_response = cache.get_exact(norm_q) if not bypass_cache else None
    if exact_cached_response:
        latency_ms = int((time.time() - start_time) * 1000)
        _exact_citations = exact_cached_response.get("citations", [])
        qa_log_id = _log_qa_with_fresh_session(
            question=question,
            answer=exact_cached_response["answer"],
            episode_ids=[c["episode_id"] for c in _exact_citations],
            latency_ms=latency_ms,
            user_ip=user_ip,
            is_cached=True,
            is_answered=len(_exact_citations) > 0,
            log_interaction=log_interaction,
            context="qa_stream_exact_cache_logging",
        )
        cached_episode_count = len({c["episode_id"] for c in _exact_citations if c.get("episode_id")})
        if cached_episode_count:
            yield f"data: {json.dumps({'type': 'status', 'message': f'Drawing from {cached_episode_count} episodes…'})}\n\n"
        yield f"data: {json.dumps({'type': 'chunk', 'text': exact_cached_response['answer']})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'citations': _exact_citations})}\n\n"
        yield f"data: {json.dumps({'type': 'follow_up', 'questions': exact_cached_response.get('follow_up_questions', [])})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'qa_log_id': qa_log_id, 'latency_ms': latency_ms, 'cached': True})}\n\n"
        return

    query_embedding = embed_text(question)

    cached_response = cache.get(norm_q, query_embedding) if not bypass_cache else None
    if cached_response:
        latency_ms = int((time.time() - start_time) * 1000)
        _cached_citations = cached_response.get("citations", [])
        qa_log_id = _log_qa_with_fresh_session(
            question=question,
            answer=cached_response["answer"],
            episode_ids=[c["episode_id"] for c in _cached_citations],
            latency_ms=latency_ms,
            user_ip=user_ip,
            is_cached=True,
            is_answered=len(_cached_citations) > 0,
            log_interaction=log_interaction,
            context="qa_stream_similarity_cache_logging",
        )
        # Stream the full cached answer as a single chunk for instant display
        cached_episode_count = len({c["episode_id"] for c in cached_response.get("citations", []) if c.get("episode_id")})
        if cached_episode_count:
            yield f"data: {json.dumps({'type': 'status', 'message': f'Drawing from {cached_episode_count} episodes…'})}\n\n"
        yield f"data: {json.dumps({'type': 'chunk', 'text': cached_response['answer']})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'citations': cached_response.get('citations', [])})}\n\n"
        yield f"data: {json.dumps({'type': 'follow_up', 'questions': cached_response.get('follow_up_questions', [])})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'qa_log_id': qa_log_id, 'latency_ms': latency_ms, 'cached': True})}\n\n"
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
            "episode": {
                "id": episode.id,
                "title": episode.title,
                "audio_url": episode.audio_url or "",
                "published_year": episode.published_at.year if episode.published_at else None,
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
            "episode": {"id": episode.id, "title": episode.title, "audio_url": episode.audio_url or "", "published_year": episode.published_at.year if episode.published_at else None},
            "similarity": cit['similarity'],
            "relevance_score": cit['relevance_score'],
            "total_relevant_chunks": cit['total_relevant_chunks'],
        })

    # ── Release the original DB session before the long streaming phase ──
    # This prevents Neon's idle-in-transaction timeout from killing the connection.
    safe_close_session(db, context="qa_stream_retrieval_phase")

    # ── Phase 2: OpenAI streaming — no DB needed ──
    # Tell the user how deep we're searching — builds trust and feels thorough
    unique_episodes = len({cp["episode"]["id"] for cp in chunk_payloads})
    yield f"data: {json.dumps({'type': 'status', 'message': f'Drawing from {unique_episodes} episodes…'})}\n\n"

    from app.qa.answer import generate_intelligent_answer_stream, _generate_basic_answer
    from app.core.config import settings

    full_answer = ""
    ranked = sorted(chunk_payloads, key=lambda c: c.get("similarity", 0), reverse=True)
    if settings.answer_generation_provider == "openai":
        try:
            for text_chunk in generate_intelligent_answer_stream(question, ranked[:6], context=context or []):
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
    import concurrent.futures

    refined_citation_chunks = (
        _select_citations_with_fresh_session(
            question=question,
            answer_text=full_answer,
            candidate_episodes=citation_payloads,
            context="qa_stream_citation_segment_selection",
        )
        if citation_payloads else []
    )
    citations = _build_citations(refined_citation_chunks) if refined_citation_chunks else []

    # ── Start follow-up generation in a background thread ──
    # This runs concurrently while we yield citations and log to the DB,
    # saving ~1–3 s that would otherwise be a blocking OpenAI call after
    # the user has already seen the full answer and citations.
    _follow_up_ctx = citation_payloads or chunk_payloads
    _follow_up_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    follow_up_future = _follow_up_executor.submit(
        _generate_follow_up_questions, question, full_answer, _follow_up_ctx
    )

    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

    # ── Phase 3: Log result with a fresh DB session ──
    latency_ms = int((time.time() - start_time) * 1000)
    qa_log_id = _log_qa_with_fresh_session(
        question=question,
        answer=full_answer,
        episode_ids=[c["episode_id"] for c in citations],
        latency_ms=latency_ms,
        user_ip=user_ip,
        is_cached=False,
        is_answered=len(citations) > 0,
        log_interaction=log_interaction,
        context="qa_stream_logging_phase",
    )

    # ── Collect follow-ups (background thread should be done by now) ──
    try:
        follow_ups = follow_up_future.result(timeout=15)
    except Exception as e:
        logger.warning("Follow-up generation failed in stream: %s", e)
        follow_ups = []
    finally:
        _follow_up_executor.shutdown(wait=False)

    yield f"data: {json.dumps({'type': 'follow_up', 'questions': follow_ups})}\n\n"
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
