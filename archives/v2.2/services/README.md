# DeFi Risk Alliance — Operational Backend

This directory contains the operational pipeline for the DeFi Risk Alliance: **ingestion** of rater data, **analytics API**, and **rating-decrease signals**. The stack is TBD (Node/TypeScript or Python); the layout is compatible with either.

## Structure

- **[ingestion/](ingestion/)** — Fetch from rater APIs, adapt to the 3-axis schema (Security, Operations, Economics per layer), compute weighted-average scores, and persist results. Run on a schedule (e.g. cron or manual).
- **[api/](api/)** — Read-only API: strategy score, layer scores, axis breakdown, and per-rater input provenance. Long-running server.
- **[signals/](signals/)** — After each ingestion (or as a dedicated job), compare latest vs previous strategy score; if it "decreases greatly" per [rules](signals/rules.md), emit webhook or notification.

## Running

- **Ingestion:** See [ingestion/README.md](ingestion/README.md). Typically run as a cron job (e.g. every 6h or daily).
- **API:** See [api/README.md](api/README.md). Start the server; it reads from the same store ingestion writes to.
- **Signals:** See [signals/README.md](signals/README.md). Can run after each ingestion run or as a separate job.

## Storage

For an operational MVP, use **SQLite** (file) or **Postgres** (hosted). Ingestion and API share the same DB. Keys and secrets (e.g. rater API keys) live in environment variables or a secrets manager, not in this repo.

## Deployment

The backend is separate from the GitHub Pages site (repo root). Deploy the API and ingestion/signals to a single process or separate workers (e.g. Vercel, Railway, or a VPS).
