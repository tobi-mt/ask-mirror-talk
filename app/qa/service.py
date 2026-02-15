import gc
import time
from sqlalchemy.orm import Session

from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map
from app.qa.answer import compose_answer
from app.storage.repository import log_qa


def answer_question(db: Session, question: str, user_ip: str):
    start_time = time.time()
    query_embedding = embed_text(question)
    retrieved = retrieve_chunks(db, query_embedding)

    episode_ids = list({chunk.episode_id for chunk, _ in retrieved})
    episode_map = load_episode_map(db, episode_ids)

    chunk_payloads = []
    for chunk, similarity in retrieved:
        episode = episode_map.get(chunk.episode_id)
        if not episode:
            continue
        chunk_payloads.append(
            {
                "text": chunk.text,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",  # Include audio URL for citations
                },
                "similarity": similarity,
            }
        )

    response = compose_answer(question, chunk_payloads)
    latency_ms = int((time.time() - start_time) * 1000)

    log_qa(
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
    }
