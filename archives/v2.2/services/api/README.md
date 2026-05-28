# Analytics API

Read-only API: current Alliance score per entity, layer breakdown (asset, market, vault with Security/Operations/Economics axes), history, and per-rater input provenance. Reads from the same store ingestion writes to.

## Endpoints

See [endpoints.md](endpoints.md) for the full spec:

- `GET /vaults` — List vaults with strategy score and layer breakdown.
- `GET /vaults/:id` — One vault: strategy score, layer scores, axis breakdown, per-rater inputs.
- `GET /vaults/:id/history` — Time series of strategy and layer scores for charts.
- `GET /vaults/:id/providers` — Input breakdown by rater.

## Running

Minimal server in [implementation/](implementation/) returns mock data until a real DB and ingestion are wired. Start with `node implementation/server.js`. Port: env `PORT` or 3000.
