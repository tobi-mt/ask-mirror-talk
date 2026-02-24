# Developer Task List (MVP)

## Phase 0 — Decisions
1. Confirm stack (FastAPI, Postgres + pgvector, faster-whisper).
2. Validate RSS feed URL and episode backlog.
3. Define response guardrails (content-only answers, no external facts).

## Phase 1 — Data + Pipeline
4. Provision Postgres with pgvector extension.
5. Create DB schema for episodes, transcripts, chunks, embeddings, and logs.
6. Build RSS ingestion pipeline.
7. Download audio assets and store locally.
8. Transcribe audio with timestamps.
9. Chunk transcript and tag metadata.
10. Generate embeddings and store in pgvector.

## Phase 2 — API
11. Implement `/ask` with retrieval and grounded response.
12. Add rate limiting and safety fallback.
13. Implement `/ingest` for manual run.
14. Add logging for observability.

## Phase 3 — WordPress
15. Build "Ask Mirror Talk" page template or block.
16. Client-side fetch to `/ask`.
17. Display citations with episode + timestamps.

## Phase 4 — Ops
18. Add scheduler for RSS polling.
19. Document deploy + config.
