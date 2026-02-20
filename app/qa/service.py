import gc
import time
from sqlalchemy.orm import Session

from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map
from app.qa.smart_citations import retrieve_chunks_two_tier
from app.qa.answer import compose_answer
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

    # Explicit garbage collection to free up memory
    gc.collect()

    return {
        "question": question,
        "answer": response["answer"],
        "citations": response["citations"],
        "latency_ms": latency_ms,
        "qa_log_id": qa_log.id,  # Include for tracking clicks and feedback
    }
