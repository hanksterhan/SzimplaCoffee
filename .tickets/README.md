# .tickets/ — Local Ticket System

SzimplaCoffee uses file-based tickets for agentic engineering. Every discrete unit of work is a YAML ticket.

## Directory Layout

```
.tickets/
├── README.md              # This file
├── open/                  # Active tickets (draft → ready → in_progress → verifying)
├── closed/                # Completed or cancelled tickets (done | cancelled)
├── events/                # Append-only transition log files
├── schema/
│   ├── ticket.schema.json # JSON Schema for ticket validation
│   └── state-machine.yaml # Valid states and transition guards
└── templates/
    └── ticket-template.yaml  # Starter template for new tickets
```

## Ticket Lifecycle

```
draft → ready → in_progress → verifying → done
                    ↓               ↓
                 blocked         in_progress (retry)
                    ↓
                 in_progress
```

Any state (except `done`) can transition to `cancelled`.

## How to Create a Ticket

1. Copy `.tickets/templates/ticket-template.yaml` to `.tickets/open/SC-N.yaml`
2. Fill in all required fields (see schema for required list)
3. Set `status: draft`
4. Create a matching execution plan at `.plans/SC-N-execution-plan.md`

## How to Transition a Ticket

1. Edit the ticket's `status` field to the new state
2. Meet the guards defined in `schema/state-machine.yaml` before transitioning
3. Append a transition event to `.tickets/events/SC-N.log`:
   ```
   2026-03-14T15:00:00Z  draft → ready  owner=h6nk-bot
   ```

### Transition Guards

| To state     | Required                                                   |
|-------------|-------------------------------------------------------------|
| `ready`     | `acceptance_criteria`, `slices`, `verification_required` all non-empty |
| `in_progress` | `delivery.branch` set                                     |
| `verifying` | All slice statuses are `complete`                          |
| `done`      | `delivery.verification.required_passed = true`, branch, commits, pr_url, completed_at, commands_run, evidence_refs |

## How to Close a Ticket

Move the YAML file from `open/` to `closed/` after setting `status: done` or `status: cancelled`.

## Verification Commands

All SzimplaCoffee tickets use these standard verification commands unless the ticket specifies overrides:

```bash
ruff check src/ tests/
pytest tests/ -v
```

For integration-level tickets, add:
```bash
pytest tests/ -v -k integration
```

## Ticket Naming

- Prefix: `SC-`
- Example: `SC-1.yaml`, `SC-12.yaml`
- Sequential integers, no padding required

## Schema Validation

To validate a ticket against the schema (requires `jsonschema` Python package):

```bash
python3 -c "
import json, yaml, jsonschema
schema = json.load(open('.tickets/schema/ticket.schema.json'))
ticket = yaml.safe_load(open('.tickets/open/SC-1.yaml'))
jsonschema.validate(ticket, schema)
print('valid')
"
```
