"""
Inspect citation candidate rejection reasons for specific questions.

Usage:
  python3 scripts/inspect_citation_candidates.py \
    "What does forgiveness require when trust has been damaged deeply?"
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

from app.core.db import get_session_local, safe_close_session
from app.indexing.embeddings import embed_text
from app.qa.smart_citations import (
    diagnose_single_quote_candidates,
    retrieve_chunks_two_tier,
    select_citation_segments,
)
from app.qa.retrieval import load_episode_map


def inspect_question(question: str) -> None:
    Session = get_session_local()
    db = Session()
    try:
        query_embedding = embed_text(question)
        retrieval_result = retrieve_chunks_two_tier(db, query_embedding)
        citation_episodes = retrieval_result["citation_episodes"]

        all_episode_ids = [cit["episode_id"] for cit in citation_episodes]
        episode_map = load_episode_map(db, all_episode_ids)

        candidate_payloads: list[dict] = []
        for cit in citation_episodes:
            episode = episode_map.get(cit["episode_id"])
            if not episode:
                continue
            candidate_payloads.append({
                "text": cit["chunk"].text,
                "start_time": cit["chunk"].start_time,
                "end_time": cit["chunk"].end_time,
                "episode": {
                    "id": episode.id,
                    "title": episode.title,
                    "audio_url": episode.audio_url or "",
                    "published_year": episode.published_at.year if episode.published_at else None,
                },
                "similarity": cit["similarity"],
                "relevance_score": cit["relevance_score"],
            })

        selected = select_citation_segments(
            db,
            question=question,
            answer_text="",
            candidate_episodes=candidate_payloads,
        )

        print("=" * 100)
        print(f"Question: {question}")
        print(f"Selected citations: {len(selected)}")
        for idx, item in enumerate(selected, 1):
            print(f"  {idx}. {item['episode']['title']} :: {item['text']}")
        print()
        print("Top candidate diagnostics are emitted via app logs when no single citation survives.")
        print("If you want explicit local candidate dumps, use the app logs from this script run.")
    finally:
        safe_close_session(db, context="inspect_citation_candidates")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Please provide at least one question.")
    for raw_question in sys.argv[1:]:
        inspect_question(raw_question)
