# Architecture Next Steps

**Date:** April 2, 2026  
**Scope:** Turn the architecture review into a practical engineering plan

## Executive Summary

Ask Mirror Talk has a strong product core: ingestion, retrieval, answer generation, citations, analytics, and a polished WordPress/PWA experience all reinforce each other. The immediate problem is not lack of capability. It is that the project's boundaries are getting blurry:

- The API layer is carrying too much product and orchestration logic.
- The database schema is partly represented in ORM models and partly only in raw SQL + migration scripts.
- The test suite does not yet protect the most important behavior reliably.
- Some core behaviors depend on environment-specific runtime conditions such as network access or cached model downloads.

This plan prioritizes safety first, then maintainability, then product leverage.

## What To Fix First

These are the highest-value, lowest-regret changes.

### 1. Fix chunk timestamp integrity

**Why it matters**

The chunk splitter is responsible for the timestamps that later power citations and audio deep links. If those times are off, the most user-visible trust signal in the whole product becomes unreliable.

**Evidence**

- [chunking.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/indexing/chunking.py#L34)

**Current risk**

- Oversized chunks are split into multiple subchunks.
- Subchunks reuse the same `end` timestamp.
- `chunk_start` is reset to the parent chunk's final end time, which can collapse or distort subsequent citation windows.

**Action**

- Refactor `chunk_segments()` / `_finalize_chunk()` so subchunk timestamps are derived from the underlying transcript segments, not from a single aggregate span.
- Add unit tests covering:
  - a chunk that stays under the limit
  - a chunk split into multiple sentence groups
  - uneven sentence lengths
  - timestamp continuity and monotonicity

**Definition of done**

- Every emitted chunk has `start <= end`
- Chunk timestamps are monotonic
- Citation timestamps map to real transcript spans

### 2. Unify push subscription schema ownership

**Why it matters**

Push is now a real subsystem, not an experiment. It handles user preference state, timezone delivery, recurring notifications, and subscriber lifecycle. That needs a single source of truth.

**Evidence**

- [main.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/api/main.py#L439)
- [models.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/storage/models.py#L119)
- [ask-mirror-talk.js](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra-child/ask-mirror-talk.js#L2124)

**Current risk**

- API writes `notify_midday`, `timezone`, and `preferred_qotd_hour`
- Notification logic reads those fields
- ORM model for `PushSubscription` does not declare them
- The schema contract is fragmented across model, raw SQL, and migration scripts

**Action**

- Update `PushSubscription` in `app/storage/models.py` to match the real schema.
- Audit notification-related tables and ensure all active columns are represented in ORM models.
- Add a compact schema verification checklist to deployment docs.
- Prefer repository/service helpers for push subscription writes instead of repeated inline SQL over time.

**Definition of done**

- ORM matches production schema for active tables
- A new engineer can infer push subscription shape without reading raw SQL

### 3. Repair the test suite so it becomes trustworthy

**Why it matters**

The current test results tell us more about naming accidents and environment coupling than about product correctness.

**Evidence**

- [test_api.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/tests/test_api.py#L10)
- [test_mmr_diversity.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/scripts/test_mmr_diversity.py)

**Observed result**

Running `.venv/bin/pytest -q` produced:

- `1 passed`
- `1 failed`
- `1 error`

**Current risk**

- `tests/test_api.py` is written as a script, but pytest collects `test_endpoint()` as a test function and fails on missing fixtures
- `scripts/test_mmr_diversity.py` is being collected even though it behaves like a manual integration script
- Model embedding tests depend on external model download behavior

**Action**

- Move script-style endpoint checks out of `tests/` or rewrite them as real pytest tests.
- Rename helper functions so pytest does not auto-collect them.
- Mark integration-only scripts clearly and keep them outside pytest discovery.
- Add a `pytest.ini` or `pyproject.toml` test discovery policy.
- Add mocking around external embedding providers where unit coverage is intended.

**Definition of done**

- `pytest` passes or fails only on meaningful application behavior
- CI does not require internet access for unit-level validation

## What To Refactor Next

These changes are worth doing after the safety fixes above.

### 4. Split the API monolith into route modules

**Why it matters**

[main.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/api/main.py) is carrying too many responsibilities:

- startup lifecycle
- ask endpoints
- QOTD and topics
- push endpoints
- analytics endpoints
- archive endpoints
- admin HTML
- rate limiting and auth helpers

This file is still readable, but it is no longer a clean boundary.

**Recommended shape**

- `app/api/routes/ask.py`
- `app/api/routes/discovery.py` for QOTD, topics, suggestions, related questions
- `app/api/routes/push.py`
- `app/api/routes/analytics.py`
- `app/api/routes/admin.py`
- `app/api/deps.py` for auth and DB-related dependencies
- `app/api/startup.py` for lifespan, cache prewarm, DB init

**Important note**

This is an organizational refactor, not a behavior rewrite. Preserve endpoints exactly while moving code.

### 5. Pull product data out of Python source

Some product content is currently embedded directly in application code:

- QOTD pool
- topic catalog
- suggested starter copy

That is fine early on, but it mixes content iteration with code deployment.

**Action**

- Move curated pools into versioned JSON or YAML files under a dedicated data directory.
- Load them through a small content access layer.
- Keep a fallback in code only if startup simplicity is essential.

**Benefit**

- Easier editing
- less merge churn
- cleaner route files

### 6. Clarify the ingestion path and retire the duplicate pipeline shape

You currently have both:

- [pipeline.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/ingestion/pipeline.py)
- [pipeline_optimized.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/ingestion/pipeline_optimized.py)

This usually means one path is historical and the other is operationally safer, but the codebase has not fully chosen.

**Action**

- Decide which ingestion path is canonical
- Make scheduler/background jobs use that path explicitly
- Move the other path into:
  - deleted code, if obsolete, or
  - clearly labeled benchmark/legacy code, if intentionally retained

**Benefit**

- Lower cognitive load
- fewer inconsistent bug fixes
- clearer production behavior

## What To Leave Alone For Now

These are good enough and should not be destabilized prematurely.

### 7. Keep the QA service shape mostly intact

The retrieval-answering flow in [service.py](/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/app/qa/service.py#L16) is one of the strongest parts of the codebase. The staged handling of:

- embeddings
- retrieval
- smart citations
- cache lookup
- DB session release before long model calls
- post-answer logging

shows sound practical thinking for a production MVP.

Refactor around it, not through it.

### 8. Keep WordPress as an integration layer, but reduce hardcoded environment assumptions

The WordPress side is product-rich and clearly important. Do not try to replace it wholesale right now.

Instead:

- remove or centralize hardcoded API base URLs
- document the contract between WordPress and the API
- consider generating a small integration spec for response shapes and SSE events

That gives you most of the benefit without reopening the entire frontend.

## Recommended Execution Order

### Phase 1: Stabilize correctness

1. Fix chunk timestamp splitting
2. Repair pytest discovery and test boundaries
3. Add unit tests around chunking, citations, and request validation

### Phase 2: Stabilize contracts

1. Bring ORM models in sync with live schema
2. Audit all raw SQL writes to tables that also have ORM models
3. Add a short schema migration ledger to docs

### Phase 3: Reduce codebase drag

1. Split `app/api/main.py` into route modules
2. Externalize curated product content
3. Choose one canonical ingestion pipeline

### Phase 4: Improve operational confidence

1. Add CI that runs unit tests in an offline-safe mode
2. Add one or two focused integration checks behind opt-in env flags
3. Add smoke coverage for `/ask`, `/ask/stream`, `/status`, and push subscription flows

## Testing Priorities

If time is limited, cover these first:

1. Chunking and timestamp correctness
2. Citation building correctness
3. `/ask` validation behavior
4. Cache hit/miss behavior for normalized questions
5. Push subscription validation and preference updates
6. Topic/QOTD endpoints returning stable schema

## Suggested Ownership By Area

This is the cleanest way to work through the refactor without everything colliding.

- **Core correctness:** `app/indexing`, `app/qa`, `tests`
- **API structure:** `app/api`
- **Schema consistency:** `app/storage`, migration scripts, push-related SQL
- **Frontend contract:** `wordpress/astra-child`, API response docs
- **Ops cleanup:** `scripts`, GitHub workflow, deployment docs

## One-Month Success Criteria

At the end of this plan, the project should feel different in these ways:

- `pytest` is a signal, not noise
- citations are trustworthy
- active schema is fully legible from code
- `app/api/main.py` is no longer the entire application
- a new contributor can understand the system by reading a few modules instead of one giant file

## Recommended First Pull Requests

If you want to break this into manageable work, do it in this order:

1. **PR 1: Fix chunk timestamps + tests**
2. **PR 2: Test suite cleanup and pytest discovery rules**
3. **PR 3: Push schema alignment**
4. **PR 4: Extract API routes from `main.py` without behavior changes**
5. **PR 5: Externalize curated content**

## Bottom Line

The project does not need a rewrite. It needs boundary restoration.

The right strategy is:

- preserve the strong retrieval/answering core
- fix correctness around timestamps and tests
- make schema ownership explicit
- modularize the API layer before more product logic accumulates there

That path keeps momentum while making the codebase safer to grow.
