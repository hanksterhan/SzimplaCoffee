# SC-93 — autopilot startup stability

## What changed

- Disabled `autopilot/policy.yaml` notification routing by clearing `notifications.session_key`.
- Closed SC-93 after confirming the configured key `telegram:-1003759576826:topic:2` has been failing repeatedly with `No session found` across multiple 2026-03-18/19 autopilot runs.

## Why it changed

- Repeated `sessions_send` failures were pure noise at the end of otherwise healthy runs.
- ByteRover rate-limit errors were also observed during the mandatory startup query step, but session logs show they were non-fatal noise rather than the real delivery blocker for this repo.
- Disabling the invalid notification route removes the recurring false-negative signal from normal autopilot cycles.

## Evidence / root cause

- `~/.openclaw/agents/sz-coffee-autopilot/sessions/684eb284-930c-4991-9bf1-d7805e74e5e5.jsonl` shows the concrete `sessions_send` failure: `No session found: telegram:-1003759576826:topic:2`.
- The same and other recent sessions also show `brv query` returning `You've reached your daily request limit`, confirming the startup ByteRover noise source.
- `sessions_list` during the SC-93 run returned only the active cron session, with no matching Telegram session key available.

## Notes for future runs

- If notification delivery is needed again, replace `notifications.session_key` with a real session key discovered via `sessions_list` at the time of configuration.
- ByteRover errors should be treated as external rate-limit noise unless they are proven to block task execution.
