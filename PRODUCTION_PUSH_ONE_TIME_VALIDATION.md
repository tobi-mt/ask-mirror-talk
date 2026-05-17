Production Push One-Time Validation (QOTD, Midday, Nightly)

Purpose
- Run a safe, one-time live validation in production.
- Confirm sends execute only for due subscribers.
- Confirm delivery ledgers increase.
- Spot-check app open and auto-submit behavior.

Safety Rules
- Run this once in a controlled window.
- Do not loop the send commands.
- Stop immediately if any command returns 5xx or unexpected large send counts.

Prerequisites
- Production API URL.
- Admin basic auth credentials.
- Database read access for verification queries.
- At least one tester device with push enabled.

Step 1: Set environment variables
- export API_BASE="https://ask-mirror-talk-production.up.railway.app"
- export ADMIN_USER="YOUR_ADMIN_USER"
- export ADMIN_PASS="YOUR_ADMIN_PASSWORD"
- export DATABASE_URL="YOUR_PRODUCTION_DATABASE_URL"

Step 2: Preflight health and auth
- curl -sS "$API_BASE/health"
- curl -sS -u "$ADMIN_USER:$ADMIN_PASS" "$API_BASE/api/push/stats"

Expected
- Health endpoint returns healthy status.
- Push stats returns totals and enabled counts.

Step 3: Capture baseline counts (before sends)
- psql "$DATABASE_URL" -c "SELECT now() AS ts_utc;"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS active_subscribers FROM push_subscriptions WHERE active = true;"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS qotd_today FROM push_qotd_history WHERE sent_at >= date_trunc('day', now());"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS midday_today FROM push_motivation_history WHERE sent_at >= date_trunc('day', now());"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS nightly_today FROM push_notification_deliveries WHERE notification_type = 'night_reflection' AND sent_at >= date_trunc('day', now());"

Step 4: Trigger one-time live sends (QOTD, Midday, Nightly)
- curl -sS -u "$ADMIN_USER:$ADMIN_PASS" -X POST "$API_BASE/api/push/send-qotd"
- curl -sS -u "$ADMIN_USER:$ADMIN_PASS" -X POST "$API_BASE/api/push/send-midday"
- curl -sS -u "$ADMIN_USER:$ADMIN_PASS" -X POST "$API_BASE/api/push/send-nightly"

Expected response shape for each
- JSON containing sent, failed, expired, total_subscribers.

Pass criteria
- sent is non-negative.
- failed is low (ideally 0; expired may be non-zero due to stale subscriptions).
- No 401/403/5xx.

Step 5: Verify ledger increments (after sends)
Run after 1-2 minutes:
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS qotd_last_10m FROM push_qotd_history WHERE sent_at >= now() - interval '10 minutes';"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS midday_last_10m FROM push_motivation_history WHERE sent_at >= now() - interval '10 minutes';"
- psql "$DATABASE_URL" -c "SELECT COUNT(*) AS nightly_last_10m FROM push_notification_deliveries WHERE notification_type = 'night_reflection' AND sent_at >= now() - interval '10 minutes';"

Optional detail checks
- psql "$DATABASE_URL" -c "SELECT notification_type, COUNT(*) FROM push_notification_deliveries WHERE sent_at >= now() - interval '10 minutes' GROUP BY notification_type ORDER BY notification_type;"
- psql "$DATABASE_URL" -c "SELECT timezone, preferred_qotd_hour, notify_qotd, notify_midday, active, COUNT(*) FROM push_subscriptions GROUP BY timezone, preferred_qotd_hour, notify_qotd, notify_midday, active ORDER BY COUNT(*) DESC LIMIT 20;"

Step 6: Spot-check open and auto-submit behavior (manual)
On one tester device:
1. Confirm push permission is enabled and app is installed/openable.
2. Tap incoming QOTD push.
3. Verify app opens to ask surface and question auto-submits.
4. Tap incoming Midday push.
5. Verify app opens and midday reflection auto-submits.
6. Tap incoming Nightly push.
7. Verify app opens and nightly reflection auto-submits.

URL simulation fallback (if no push arrives during this check)
- Open in browser:
  - "$API_BASE/ask-mirror-talk/?autoask=What%20is%20one%20honest%20question%20for%20today%3F#ask-mirror-talk-form"
  - "$API_BASE/ask-mirror-talk/?midday_reflection=1#ask-mirror-talk-form"
  - "$API_BASE/ask-mirror-talk/?night_reflection=1#ask-mirror-talk-form"

Expected behavior
- Input fills and submit starts automatically.
- Result response renders without manual submit tap.

Step 7: Final quick sanity snapshot
- curl -sS -u "$ADMIN_USER:$ADMIN_PASS" "$API_BASE/api/push/stats"
- psql "$DATABASE_URL" -c "SELECT now() AS completed_at_utc;"

Abort conditions
- Any send endpoint returns 5xx.
- failed spikes unexpectedly relative to total_subscribers.
- Repeated sends are attempted in the same window.

Rollback / mitigation if issues found
- Temporarily disable notification jobs (pause cron service).
- Keep endpoints but stop scheduler start command until fixed.
- For stale endpoints: allow expired cleanup to continue via normal sends.

Alternative single-command server-side run
If you have shell access inside the production worker with environment already loaded:
- python3 scripts/send_due_push_notifications.py

This runs QOTD + Midday + Streak + Nightly in one hourly-safe pass with existing due-window and de-dup logic.
