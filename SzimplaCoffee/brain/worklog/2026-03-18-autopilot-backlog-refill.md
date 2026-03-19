# 2026-03-18 - autopilot backlog refill

Autopilot ran a backlog-refill cycle because ready work had dropped below the policy minimum.

Created:

- SC-81 — add purchase handoff CTA from recommendation results
- SC-82 — add stale and failed crawl badges to Watch page merchant rows

Why these tickets:

- SC-81 closes the missing UX loop after SC-78 taught purchases to accept `recommendationRunId`
- SC-82 turns the existing crawl-health fields from SC-74 into actionable watch-queue visibility

Verification completed:

- `python3 ~/.agents/skills/create-tickets/scripts/ticket_cli.py ticket validate --ticket .tickets/open/SC-81.yaml --schema ~/.agents/skills/create-tickets/references/ticket-schema.json --state-machine ~/.agents/skills/create-tickets/references/state-machine.yaml`
- `python3 ~/.agents/skills/create-tickets/scripts/ticket_cli.py ticket validate --ticket .tickets/open/SC-82.yaml --schema ~/.agents/skills/create-tickets/references/ticket-schema.json --state-machine ~/.agents/skills/create-tickets/references/state-machine.yaml`
