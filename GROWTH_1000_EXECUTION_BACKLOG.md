# Ask Mirror Talk — Growth To First 1000 Users

## Objective
Reach the first 1000 unique users with strong activation and retention loops while preserving calm, trust, and reflection quality.

## North-Star Metrics
1. Activation rate: `question_submitted` within first session.
2. Time-to-first-aha: app open to first answer shown.
3. D1 and D7 retention.
4. Share rate: users with `share_cta_used` / active users.
5. Guided-entry usage: users with `question_origin_selected` from guided sources.

## Implemented In This Phase (Safe Rollout)
1. Starter journeys in Ask panel with mood-aware prompts.
2. First-3-wins activation checklist with local progress memory.
3. Activation instrumentation via `activation_step_completed`.

## Event Spec (v1)
1. `question_submitted`
- Trigger: user submits the ask form.
- Required metadata: `origin`, `length`.
- Success threshold: >= 65% of first-time sessions.

2. `question_origin_selected`
- Trigger: any guided/typed origin selection.
- Required metadata: `origin`.
- Success threshold: >= 45% guided origins among first-time users.

3. `activation_step_completed`
- Trigger: checklist steps completed.
- Required metadata: `step`, `completed_count`.
- Success threshold: >= 40% users reach 2/3 in first session; >= 22% reach 3/3 in first 3 days.

4. `share_cta_used`
- Trigger: reflection card or invite share action.
- Required metadata: `action`, optional `method`.
- Success threshold: >= 12% of active users within first 14 days.

5. `reflection_note_saved`
- Trigger: private note saved.
- Required metadata: `prompt`, `length`.
- Success threshold: >= 18% of first-week actives.

## UX Success Criteria
1. First action visible in under 2 seconds from app load.
2. Blank-state avoidance: users always see a suggested next step.
3. Activation card completion path is one tap from each step.

## Next Safe Iteration
1. Add experiment IDs to starter-journey variants (`starter_v1`, `starter_v2`).
2. Add a lightweight progress recap banner after 3 completed sessions.
3. Add deep-link campaign map from UTM theme to preferred starter journey.

## Release Checklist
1. Verify no console errors on app open, submit, and share flow.
2. Verify checklist state persists across refresh.
3. Verify checklist auto-hides at 3/3 completion.
4. Verify event emission volume in analytics backend.
5. Verify mobile layout for Ask panel components (<= 390px width).
