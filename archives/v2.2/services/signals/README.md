# Signals — Rating-Decrease Notifications

When a strategy's overall score (composed from asset, market, and vault layers) decreases greatly (see [rules.md](rules.md)), we emit a signal: webhook or notification.

## Rules

See [rules.md](rules.md). Summary: alert if numeric drop > 2.0 or score below 4.0 (configurable).

## Mechanism

- **Input:** Latest and previous strategy scores per entity (from DB; same data ingestion writes).
- **Process:** After each ingestion run (or a dedicated job), compare latest vs previous strategy score for each entity; if the rule triggers, call webhook or push to queue.
- **Output:** Webhook payload (e.g. `{ entity_id, previous: { letter, numeric }, current: { letter, numeric }, rule_triggered }`) or integration-specific format.

## Running

- Option A: Run as part of the ingestion job (after persist step).
- Option B: Separate script/job that reads last two scores per entity from DB and emits. See [implementation/](implementation/) for a script that checks one entity and logs "would alert" so the flow is clear.

## Config

- `SIGNALS_WEBHOOK_URL` — Optional. If set, POST payload to this URL when rule triggers.
- Rule thresholds (grade drop, numeric drop, minimum score) can be env or config file; document when fixed.
