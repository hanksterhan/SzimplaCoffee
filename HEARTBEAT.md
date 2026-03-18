# Heartbeat — SzimplaCoffee Autopilot Oversight

Inspect autopilot state for the SzimplaCoffee project and surface only actionable exceptions.
Do not perform delivery work. Read files only.

## Check Procedure

1. Read `autopilot/status.json`
2. Read `autopilot/approvals.jsonl` — scan for any `"status": "pending"` entries
3. Read `.tickets/open/` — count tickets with `status: ready`
4. Check `status.json → task_failures` for any task with failure count ≥ 2
5. Read `autopilot/goal.yaml` — compare `success_criteria` against closed ticket history if readily available

## Report Conditions (alert only if true)

Report **only** when one or more of these conditions holds:

| Condition | Alert Text |
|-----------|-----------|
| Any `pending` approval in `approvals.jsonl` | ⚠️ **Autopilot blocked** — pending approval: `<id>` reason: `<reason>` |
| Any task with failure count ≥ 2 in `task_failures` | ⚠️ **Task stuck** — `<task_id>` has failed twice, needs human review |
| Zero ready tasks AND `last_refill_at` is recent (refill already ran) | ⚠️ **Backlog empty** — no ready tasks remain and refill did not produce new tickets |
| All `success_criteria` satisfied | ✅ **Mission complete** — all success criteria met, autopilot should stop |

## Silence Condition

If **none** of the above conditions are true, respond with exactly:

```
HEARTBEAT_OK
```

Do not summarize normal status. Do not report task counts, timestamps, or run history unless an alert condition is active.
