# Analytics API — Endpoints

Read-only API for current Alliance scores, history, and per-rater input breakdown. Data source: same store ingestion writes to.

## Base

- Base URL: TBD (e.g. `https://api.defiriskalliance.org` or localhost when running locally).
- All responses JSON. Optional: `?format=webhook` for compact payloads where supported.

## Endpoints

### GET /vaults

List vaults with their strategy score and layer breakdown.

- **Query:** Optional `chain_id`, `protocol_slug` to filter.
- **Response:** Array of `{ entity_id, score, layers: { asset: { score, security, operations, economics }, market: { ... }, vault: { ... } }, methodology_version, updated_at }`.

### GET /vaults/:id

One vault: strategy score, layer scores, axis breakdown, and per-rater inputs.

- **Response:** `{ entity_id, score, layers: { asset: { score, security, operations, economics }, market: { ... }, vault: { ... } }, methodology_version, updated_at, inputs_by_provider: { rater: { asset: { ... }, market: { ... }, vault: { ... } } }, composition?: { assets[], markets[] } }`.

### GET /vaults/:id/history

Time series of the strategy score and layer scores for charts.

- **Query:** Optional `from`, `to` (ISO date), `granularity` (e.g. day).
- **Response:** Array of `{ timestamp, score, layers: { asset: { ... }, market: { ... }, vault: { ... } } }`.

### GET /vaults/:id/providers

Current input breakdown by rater: which axis scores each rater supplied per layer.

- **Response:** `{ entity_id, providers: { rater: { asset: { security, operations, economics }, market: { ... }, vault: { ... }, timestamp } } }`.

## Entities

- **Vault** `:id` = `chain_id:vault_address` or `chain_id:protocol_slug:vault_id` (same as in methodology).
- Asset and market endpoints (e.g. `GET /assets/:id`, `GET /markets/:id`) can be added later; vaults are first-class for now.
