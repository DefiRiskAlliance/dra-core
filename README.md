# DeFi Risk Alliance — aggregate stage scoring (v3.0)

A Python library that aggregates external risk providers into a single DeFi
**strategy stage** (`0`, `1`, or `2`) using the **DeFi Risk Alliance** v3.0
methodology. The rendered spec lives at
[defiriskalliance.github.io/methodology](https://defiriskalliance.github.io/methodology.html);
this repository is the reference implementation. The canonical registry is
[`methodology/criteria.py`](./methodology/criteria.py) and the engine is
[`methodology/engine.py`](./methodology/engine.py).

## What changed vs v2.2

The 0–10 numeric score is gone. Every cell is now scored as a discrete
**Stage 0 / 1 / 2**, computed from an open registry of named criteria, and
rolled up by the *weakest-link* rule.

| | DRA v2.2 | DRA v3.0 |
|--|---------|----------|
| Cell value | 0–10 weighted average | Stage 0/1/2, max stage whose criteria are all satisfied |
| Layer rollup | Weighted average of axes | `min` over the three components |
| Strategy rollup | Weighted average of layers | `min` over the layers applicable to the mode |
| Provider output | `CellContribution(score=…)` | `CriterionAttestation(verdict=…)` |

The full v2.2 specification and its operational scripts are preserved under
[`archives/v2.2/`](./archives/v2.2/) for historical reference and
score-reproducibility.

## Layers, components, stages

- **Layers:** `asset`, `market`, `vault` (plus optional meta-vault, recursive).
- **Components:** `security` (op-sec + smart-contract), `operations` (legals,
  governance, oracles, withdrawal mechanics), `strategy_economics`
  (peg/collateral, market parameters, vault strategy risk).
- **Stages:**
  - **0** — Inadequate / Unverified. Default-to-worse.
  - **1** — Production-grade. Audited, multisig + timelock, public docs,
    conservative parameters.
  - **2** — Mature / Decentralised. Long Lindy, multiple audits, immutable or
    long-timelock governance, transparent reserves.

Each (layer, component) cell publishes an explicit set of criteria for Stage 1
and Stage 2 — see [`methodology/criteria.py`](methodology/criteria.py).

## Quick start

```bash
pip install -r requirements.txt
python examples/dra_score.py
```

```python
from methodology import DRAEngine, StrategyContext
from providers import DefiscanRater, PharosRater, XerberusRater

engine = DRAEngine([DefiscanRater(), PharosRater(), XerberusRater()])
ctx = StrategyContext(
    mode="C",
    asset_is_stablecoin=True,
    xerberus_asset_symbol="USDC",
    pharos_stablecoin_id="usdc-circle",
    defiscan_market_slug="aave-v3",
    xerberus_protocol_slug="aave-v3",
)
result = engine.score(ctx)
print(result.strategy_stage, result.layer_stages)
for status in result.unsatisfied_criteria():
    print(status.criterion.id, status.criterion.description)
```

## Composition modes

| Mode | Layers | Strategy stage |
|------|--------|----------------|
| A — Vault strategy | asset + market + vault | `min(asset, market, vault)` |
| B — Direct vault | asset + vault | `min(asset, vault)` |
| C — Market position | asset + market | `min(asset, market)` |
| D — Meta-vault | asset + meta-vault + each underlying vault | `min(asset, meta_vault, min(underlying))` |

## Bundled providers (`providers/`)

| Provider | Anchors |
|----------|---------|
| `XerberusRater` | Public dendrogram → asset operations + economics; protocol → market & vault security/operations/economics. |
| `PharosRater` | `PHAROS_API_KEY`. Bluechip grade → asset security; report-card dimensions → asset operations + economics; DEX liquidity → asset economics. |
| `PhilidorRater` | Public REST → vault (and optional market) security/operations/economics; non-stable asset cells. |
| `WebacyRater` | `WEBACY_API_KEY`. Vault overall risk → vault security verification or violation. |
| `StakingRewardsRater` | `STAKING_REWARDS_API_KEY`. Per-strategy security/operations/strategy → market + vault. |
| `YearnCurationRater` | HTML curation reports → market + vault. |
| `DefiscanRater` | Curated DeFiScan stage map → market.operations and vault.operations criteria. |

Each provider keeps its mapping table at the top of its file, so changes are
visible in code review.

## How aggregation works

For every criterion `c`:

- If at least one provider files `verified` AND no provider files `violated` →
  `c` is satisfied.
- If any provider files `violated` → `c` is unsatisfied (default-to-worse).
- If no attestations exist or all are `unknown` → `c` is unsatisfied.

Then `cell_stage = max N ∈ {0,1,2}` such that every criterion at every stage
`1..N` for that cell is satisfied. Layer = `min` over components. Strategy =
`min` over applicable layers.

## Tests

```bash
pytest tests/ -q
```

## Docs

- [`PROVIDER_GUIDE.md`](PROVIDER_GUIDE.md) — writing a provider adapter.
- [`methodology/criteria.py`](methodology/criteria.py) — the rubric.

## Public site (`docs/`)

The repository ships a static GitHub Pages site under [`docs/`](docs/):

- [`docs/index.html`](docs/index.html) — Charter (renders [`docs/content.md`](docs/content.md) via `marked.js`).
- [`docs/methodology.html`](docs/methodology.html) — Methodology, written against the v3.0 Stage 0/1/2 ratchet implemented here.
- [`docs/ratings.html`](docs/ratings.html) — A snapshot of ratings for a curated set of vaults, fetched client-side from [`docs/ratings.json`](docs/ratings.json).

Regenerate the snapshot whenever raters or the curated entry list change:

```bash
python3 examples/dra_site_snapshot.py
```

This calls the engine with the four production raters (Pharos, Yearn Risk
Curation, Philidor, Vaultscan) over the entries in
[`examples/dra_site_snapshot.py`](examples/dra_site_snapshot.py) and writes a
small JSON file consumed by `ratings.html`. API keys are loaded from `.env`.

Preview the site locally:

```bash
python3 -m http.server --directory docs 8000
# open http://localhost:8000
```

## Deployment

The live site at [defiriskalliance.github.io](https://defiriskalliance.github.io/)
is published from a separate repo (`DefiRiskAlliance/defiriskalliance.github.io`)
that only holds the contents of `docs/` flattened to the root. A GitHub Actions
workflow ([`.github/workflows/publish-docs.yml`](.github/workflows/publish-docs.yml))
syncs the two repos automatically.

**Shipping a new vault rating now looks like this:**

```bash
# 1. Add your entry to ENTRIES in examples/dra_site_snapshot.py
# 2. Regenerate the snapshot
python3 -m examples.dra_site_snapshot
# 3. Commit and push to main
git add examples/dra_site_snapshot.py docs/ratings.json
git commit -m "ratings: add <vault name>"
git push origin main
```

That's it. The workflow runs on push, subtree-splits `docs/`, and pushes it
to the Pages repo. GitHub Pages rebuilds in ~30–60 seconds.

### One-time setup for the publish workflow

The workflow needs to push to a different repo, which requires a token:

1. Generate a [fine-grained Personal Access Token](https://github.com/settings/personal-access-tokens/new)
   - Resource owner: `DefiRiskAlliance`
   - Repository access: `DefiRiskAlliance/defiriskalliance.github.io` only
   - Permission: **Contents → Read and write**
2. On `DefiRiskAlliance/dra-core`, go to **Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `PAGES_PUBLISH_TOKEN`
   - Value: the PAT from step 1

Once the secret is set, every push to `main` that touches `docs/` triggers a
deploy. You can also run it manually from the Actions tab via the
"Run workflow" button (`workflow_dispatch`).

### Manual fallback

If CI is broken, the manual command still works:

```bash
git subtree split --prefix=docs -b dra-publish
git push dra dra-publish:main
```

(Assumes a remote named `dra` pointing at
`https://github.com/DefiRiskAlliance/defiriskalliance.github.io.git`.)
