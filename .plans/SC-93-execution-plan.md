# SC-93 Execution Plan

## Goal

Resolve the apparent autopilot startup failures for SzimplaCoffee by fixing the concrete startup-noise sources: ByteRover rate-limit behavior during startup context gathering and invalid notification session routing.

## Context

Recent `sz-coffee-autopilot` session logs show two repeated startup-path issues:

1. ByteRover query attempts hit a daily request limit during startup/context gathering.
2. `policy.notifications.session_key` is set to `telegram:-1003759576826:topic:2`, but `sessions_send` reports `No session found` for that key.

Even when the run otherwise proceeds, this makes startup appear broken and reduces trust in autopilot.

## Files / Areas Expected to Change

| File | Change |
|------|--------|
| `autopilot/policy.yaml` | Fix or disable invalid notification routing |
| `autopilot/status.json` | Refresh next-run hint/state after stabilization if needed |
| `autopilot/goal.yaml` | Read-only context |
| `~/.openclaw/agents/sz-coffee-autopilot/sessions/*.jsonl` | Read-only evidence source |
| OpenClaw agent/autopilot config | Smallest verified config change needed to remove startup noise |

## Implementation Steps

1. Inspect the most recent `sz-coffee-autopilot` session logs and isolate the exact startup failure/noise sequence.
2. Confirm whether ByteRover errors are fatal, non-fatal, or only noisy for the current startup path.
3. Fix notification routing:
   - resolve the correct target session key if one exists, or
   - disable `notifications.session_key` cleanly until a valid route is available.
4. Adjust the startup path/config so ByteRover rate-limit issues do not present as startup failure for SzimplaCoffee autopilot.
5. Run one bounded autopilot cycle and verify:
   - no invalid notification routing error,
   - no startup path that appears broken,
   - checkpoint/status update correctly.

## Risks / Notes

- The root cause may live partly in agent/global OpenClaw config rather than only repo config.
- Avoid broad OpenClaw changes; prefer a narrow fix for `sz-coffee-autopilot`.
- If ByteRover is globally mandated by another skill path, handle the rate-limit failure gracefully rather than trying to remove the tool entirely without evidence.

## Verification

- Inspect recent session logs and capture exact evidence of failure/noise.
- Run one autopilot cycle after the fix.
- Confirm no `No session found` notification error appears.
- Confirm startup no longer appears to fail due to ByteRover rate-limit noise.

## Out of Scope

- Reworking the full autopilot workflow
- Fixing unrelated autopilot agents
- Large OpenClaw version/config migration
