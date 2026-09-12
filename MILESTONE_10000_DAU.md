# Ask Mirror Talk: 10,000 Daily Active Users

## North star

Reach 10,000 daily active users (DAU) without sacrificing answer trust, user wellbeing, or product reliability.

DAU is defined as the number of distinct device IDs that open Ask Mirror Talk during a UTC calendar day. IP address is used only as a fallback when browser storage is unavailable. This measures product visitors; question askers alone are not a valid DAU denominator.

## Product scorecard

The authenticated `GET /api/analytics/growth?days=30` endpoint is the source for the first operating scorecard.

| Metric | Definition | Why it matters |
| --- | --- | --- |
| DAU | Distinct daily openers | North-star reach |
| Visitor-to-question rate | Daily askers / DAU | First-value activation |
| Visitor-to-value rate | Users who save, share, or open a source / DAU | Meaningful outcome, not empty engagement |
| Day-1 retention | Eligible openers who return the next UTC day | Early habit signal |
| Referrers | Users who use the referral CTA | Organic growth input |
| Answer success and satisfaction | Answered rate and positive feedback | Trust guardrails |
| P95 latency | 95th percentile answer latency | Experience guardrail |

Targets below are provisional until 14 complete days of clean `app_opened` data exist:

- Visitor-to-question: 35% or higher
- Visitor-to-value: 12% or higher
- Day-1 retention: 25% or higher
- Answer success: 95% or higher
- Positive feedback: 85% or higher, with at least 100 ratings in the window

## Growth model

The milestone should be managed as a system:

`DAU = new visitors activated + retained visitors + referred visitors reactivated`

Acquisition should not be scaled until the first-question flow reliably creates value. A practical sequence is:

1. **Measure (now):** collect clean DAU, activation, value, retention, source, and referral data.
2. **Activate:** simplify the first screen around one emotionally safe question and test guided entry versus free text.
3. **Retain:** turn saved insights, gentle reminders, and continuing reflection threads into a useful return habit.
4. **Refer:** make beautiful, privacy-safe reflection cards and one-to-one invitations the core organic loop.
5. **Distribute:** build searchable episode/topic landing pages and creator partnerships after conversion and retention clear their guardrails.

## First 30-day execution plan

### Days 1-7: trustworthy baseline

- Deploy `app_opened` tracking and the growth scorecard.
- Verify event coverage, bot/internal traffic exclusions, UTC cutoffs, and device-ID persistence.
- Record the baseline by entry source, device class, and web versus installed PWA.
- Do not interpret partial first-day retention data as a trend.

### Days 8-14: activation experiment

- Compare a focused guided-question entry against the current multi-option first screen.
- Primary metric: visitor-to-first-question rate.
- Guardrails: answer success, negative feedback, abandonment, and P95 latency.
- Ship only if activation improves without a meaningful guardrail regression.

### Days 15-21: return-value experiment

- Test a post-answer continuation that lets users save one insight and choose when to revisit it.
- Primary metric: day-1 and day-7 return rate by exposure cohort.
- Keep private notes local unless the user explicitly chooses to sync them.

### Days 22-30: referral experiment

- Test one-to-one invitation copy and share-card presentation after a high-quality answer.
- Measure CTA shown, CTA used, referred landing, referred first question, and referred day-1 return.
- Avoid mass-share pressure and suppress referral prompts after weak or fallback answers.

## Scale gates

- **0-500 DAU:** repair instrumentation and first-question activation.
- **500-2,000 DAU:** prove repeat use and one dependable acquisition channel.
- **2,000-5,000 DAU:** expand SEO/topic surfaces and podcast/creator distribution.
- **5,000-10,000 DAU:** scale only channels whose referred cohorts retain and receive trustworthy answers.

Every weekly review should end with one explicit decision: keep, iterate, stop, or scale the current experiment.
