# Ingestion — Rater Data to Alliance Score

Fetch from rater APIs, map responses into the **3-axis schema** (Security, Operations, Economics — each 0–10 per layer), aggregate across raters, compute layer and strategy scores, and persist results.

## Flow

1. **Fetch** — For each entity (asset, market, vault), call each rater's API (or use adapters that already have data).
2. **Adapt** — Each adapter outputs the 3-axis schema per entity, per rater. See [PROVIDER-INTEGRATION.md](../../docs/PROVIDER-INTEGRATION.md) for the canonical JSON format.
3. **Aggregate** — For each cell (layer x axis), compute the weighted average of all rater scores. Raters have equal weight by default; the Alliance can adjust weights per rater (including setting to 0 to dismiss). See [METHODOLOGY.md — Multi-Rater Aggregation](../../docs/METHODOLOGY.md#6-multi-rater-aggregation).
4. **Score** — Compute layer scores (weighted sum of axes: 30/30/40 for assets and markets, 40/40/20 for vaults) and strategy score (weighted sum of layers per composition mode). Output: 0–10 numeric + letter grade, tagged with `methodology_version`.
5. **Persist** — Store aggregated axis scores, layer scores, strategy score, and per-rater provenance.

## Schedule

Run ingestion on a schedule (e.g. daily or every 6h). Use cron, a job queue, or a manual trigger. Document the schedule here when fixed.

## Adapters

Adapters live in [adapters/](adapters/). Each adapter:

- Takes rater API config (e.g. base URL, API key from env).
- Fetches data for one or more entities.
- Returns a list of input records: `entity_type`, `entity_id`, `provider`, `dimensions` (security, operations, economics — each 0–10 or null), `timestamp`.

**Flexible coverage:** A rater can cover as little as one axis for one layer. There is no requirement to supply all three axes. Each non-null axis score participates independently in the weighted average for its cell. See [METHODOLOGY.md](../../docs/METHODOLOGY.md) Section 6.1.

See [adapters/mock.js](adapters/mock.js) for an example.
