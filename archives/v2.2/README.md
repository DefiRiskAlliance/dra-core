# DRA v2.2 — archived

This directory is a frozen snapshot of the **DeFi Risk Alliance v2.2** methodology
and its accompanying operational scripts. It is kept here for historical
reference and reproducibility of v2.2-tagged scores.

> **v2.2 is no longer the active methodology.** The current production version is
> **v3.0**, which lives at the root of this repo (`methodology/`, `providers/`,
> `examples/`). Start there for any new work.

## What v2.2 was

A 0–10 numeric risk score aggregated from independent external raters across
three layers (Asset, Market, Vault) and three axes (Security, Operations,
Economics). Composition modes A/B/C/D describe how a strategy combines those
layers. Weights between raters were tunable and versioned alongside the
methodology.

See [METHODOLOGY.md](./METHODOLOGY.md) for the full v2.2 specification and
[PROVIDER-INTEGRATION.md](./PROVIDER-INTEGRATION.md) for the rater-onboarding
contract.

## Why v3.0 replaced it

| | v2.2 | v3.0 |
|---|---|---|
| Output | continuous 0–10 score | discrete Stage 0 / 1 / 2 |
| Aggregation | weighted average across raters | named criteria + weakest-link roll-up |
| Missing evidence | reduces weight, doesn't fail | **default-to-worse**: unattested ⇒ unsatisfied |
| Rater fitness | bilateral integrations | each rater declares which criteria it covers |
| Disagreement | weights smooth it away | resolved per-criterion, visible in audit log |

The v3.0 changes are summarised in the top-level [README.md](../../README.md)
and detailed in [methodology/criteria.py](../../methodology/criteria.py) and
[methodology/engine.py](../../methodology/engine.py).

## Provenance

This snapshot was taken from
[`Octave-byte/defiriskalliance@05be1a2`](https://github.com/Octave-byte/defiriskalliance/commit/05be1a2)
— the last commit before the v3.0 rebuild. Full v2.x git history remains in
that repo until it is formally archived.

## Layout

```
archives/v2.2/
├── METHODOLOGY.md             # The v2.2 spec
├── PROVIDER-INTEGRATION.md    # Rater onboarding contract
├── methodology.html           # The v2.2 methodology page as published at the time
└── services/                  # Operational scripts (Node.js)
    ├── api/                   # HTTP server exposing v2.2 scores
    ├── ingestion/             # Per-rater adapters
    └── signals/               # Alert rules and evaluator
```

## Reproducing a v2.2 score

The `services/` tree is preserved as-is. It targets Node.js and expects rater
adapters under `services/ingestion/adapters/`. The included `mock.js` adapter
is illustrative — production v2.2 used external rater payloads with the
schema documented in `PROVIDER-INTEGRATION.md`. Nothing in this archive is
maintained; treat it as read-only history.
