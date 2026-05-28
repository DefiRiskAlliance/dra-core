# DeFi Risk Alliance — Risk-Scoring Methodology

This document defines the DeFi Risk Alliance's methodology for scoring DeFi strategies. Every strategy is decomposed into up to three **layers** — Assets, Markets, and Vaults — each evaluated on three **axes** — Security, Operations, and Economics. Definitions of markets vs vaults are in [MARKETS-VS-VAULTS.md](MARKETS-VS-VAULTS.md).

**Methodology version:** v2.2

---

## 1. Overview

The Alliance rates the risk of DeFi yield strategies. A strategy is a composition of layers:

| Layer | What it represents | Examples |
|-------|--------------------|----------|
| **Asset** | The underlying token(s) | USDC, ETH, stETH, wBTC |
| **Market** | A lending/borrowing venue where assets are deployed | Aave USDC supply, Compound ETH market, Fluid lending pool |
| **Vault** | An ERC-4626 / strategy vault or CDP that allocates across markets | Morpho vault, Yearn vault, Maker CDP etc.|

An optional fourth layer, **Meta-vault**, aggregates multiple vaults. When present it is treated as a vault whose underlying positions are other vaults; the same vault-level methodology applies recursively.

Each layer is scored on three axes:

| Axis | What it captures |
|------|------------------|
| **Security** | On-chain technical security: code maturity, audits, bug bounties |
| **Operations** | Governance, transparency, compliance, operational controls |
| **Economics** | Intrinsic economic quality: peg stability, collateral, liquidity, strategy risk |

This produces a **3 × 3 matrix** of scores. Each cell is a **0–10** value supplied by one or more external risk providers. Higher is safer.

---

## 2. Entity Identity

Every scored entity is uniquely identified by:

- **Asset:** `chain_id` + `token_address` (or canonical symbol where agreed).
- **Market:** `chain_id` + `protocol_slug` + `market_id` (e.g. USDC supply on Aave Ethereum).
- **Vault:** `chain_id` + `vault_address` (or `protocol_slug` + `vault_id`).

---

## 3. Axis Definitions

### 3.1 Security

Security measures on-chain technical robustness — how likely the smart contracts are to be exploited.

| Layer | What providers assess | Guidance |
|-------|----------------------|----------|
| **Asset** | Contract maturity (Lindy effect — time live without exploit), live bug bounty program, audit coverage and recency | Longer track record without incident, active and well-funded bug bounty, multiple independent audits from reputable firms all increase the score. Inspired by Credora's *Contract Maturity* and *Audit Quality* modifiers. |
| **Market** | Protocol Lindy (time without exploit), bug bounty program, audit history and breadth of coverage | Same principles as asset security, applied to the lending protocol's contracts. Consider the scope of audits relative to contract complexity. |
| **Vault** | Vault contract Lindy, bug bounty, audit status | Vault-specific contracts may be younger or less audited than the underlying protocol. Evaluate the vault layer independently. |

### 3.2 Operations

Operations captures how each layer is governed, documented, and run day-to-day.

| Layer | What providers assess | Guidance |
|-------|----------------------|----------|
| **Asset** | Documentation transparency, reserve status and on-chain verifiability, legal and regulatory compliance | For stablecoins: proof-of-reserves, attestation frequency, issuer jurisdiction, and licenses (cf. Credora's *Reserves Transparency*, *Regulatory Cover*, *User Rights*). For non-stablecoins: documentation quality and governance clarity. |
| **Market** | Governance structure (timelock duration, multisig composition), oracle quality and diversity, parameter management (LTV, caps, liquidation thresholds) | Longer timelocks, credible multisigs, high-quality oracle feeds (e.g. Chainlink, RedStone, dual-oracle setups), and conservative parameter setting all increase the score. Cf. Credora's *Governance* modifier and Staking Rewards' Operations pillar. |
| **Vault** | Governance controls (timelocks, immutability, depositor reaction window), withdrawal liquidity (lockups, delays, caps), pause capability and upgrade path | Immutable or long-timelock vaults score higher. Instant withdrawal with no lockup scores higher. Pause capability is a double-edged sword — beneficial for emergency response but a centralization vector. Cf. Credora's *Guardian* and *Timelock* modifiers. |

### 3.3 Economics

Economics reflects the intrinsic economic quality of the asset or the riskiness of the strategy.

| Layer | What providers assess | Guidance |
|-------|----------------------|----------|
| **Asset** | Depeg risk (historical peg deviation, drawdown severity), collateral quality (backing type, reserve composition), liquidity depth (on-chain depth, spread, venue diversity) | For stablecoins: peg track record, reserve adequacy, and on-chain liquidity are primary factors (cf. Credora's *Peg Track Record*, *Collateralization*, *Asset Quality*). For volatile assets: historical volatility, market cap, and DEX/CEX liquidity. |
| **Market** | Strategy riskiness given market volatility, liquidation risk (LTV health, liquidation efficiency), concentration risk (single-asset dominance, utilization rate) | How well the market parameters protect against loss under adverse conditions. High utilization, thin liquidation buffers, and volatile collateral reduce the score. |
| **Vault** | Overall strategy risk based on the positions the vault takes — leverage, directionality, complexity of the yield strategy | Vault economics can reflect the weighted quality of underlying market positions, but providers score it independently. Simple single-market supply vaults score higher than complex leveraged or multi-leg strategies. Cf. Credora's *Anchor PSL* (weighted average of underlying market risk) and Staking Rewards' Strategy pillar. |

---

## 4. Scoring

### 4.1 Provider Inputs

Each of the 9 cells (3 layers × 3 axes) is scored **0–10** by external risk providers:

|  | Security | Operations | Economics |
|--|----------|------------|-----------|
| **Asset** | 0–10 | 0–10 | 0–10 |
| **Market** | 0–10 | 0–10 | 0–10 |
| **Vault** | 0–10 | 0–10 | 0–10 |

**Higher is safer.** A score of 0 represents the worst possible risk; 10 represents the lowest observable risk.

Missing or unverifiable data is treated as **0** (default-to-worse). Transparency is a risk factor: if a provider cannot assess a dimension, the score must reflect that uncertainty.

### 4.2 Layer Scores

Each layer's score is the weighted average of its three axes. Weights differ by layer to reflect what matters most at each level:

**Assets and Markets** — economics (strategy/asset quality) carries the most weight:

| Axis | Weight |
|------|--------|
| Security | 30% |
| Operations | 30% |
| Economics | 40% |

```
asset_score  = 0.30 × asset_security  + 0.30 × asset_operations  + 0.40 × asset_economics
market_score = 0.30 × market_security + 0.30 × market_operations + 0.40 × market_economics
```

**Vaults** — security and operations (infrastructure risk) dominate because vault economics often derive from underlying markets:

| Axis | Weight |
|------|--------|
| Security | 40% |
| Operations | 40% |
| Economics | 20% |

```
vault_score = 0.40 × vault_security + 0.40 × vault_operations + 0.20 × vault_economics
```

The rationale: vault economics can frequently be approximated as the weighted sum of the quality of underlying markets. Since providers may not update vault economics on every rebalance, the Alliance decouples them and gives more weight to the vault's own infrastructure security and operational controls.

Each layer score is a value in **0–10**.

### 4.3 Composition Modes

The overall strategy score is the weighted average of the applicable layer scores. Four composition modes cover the main DeFi product types:

**Mode A — Vault strategy** (vault deploys into lending markets):

| Layer | Weight |
|-------|--------|
| Asset | 20% |
| Market | 40% |
| Vault | 40% |

```
strategy_score = 0.20 × asset_score + 0.40 × market_score + 0.40 × vault_score
```

**Mode B — Direct vault** (vault holds assets directly, CDP-style, no intermediate market):

| Layer | Weight |
|-------|--------|
| Asset | 35% |
| Vault | 65% |

```
strategy_score = 0.35 × asset_score + 0.65 × vault_score
```

**Mode C — Market rating** (lending/borrowing position with no vault layer):

| Layer | Weight |
|-------|--------|
| Asset | 35% |
| Market | 65% |

```
strategy_score = 0.35 × asset_score + 0.65 × market_score
```

**Mode D — Meta-vault** (see Section 4.4 below).

The strategy score is always a single value in **0–10**.

### 4.4 Meta-Vaults

A meta-vault aggregates multiple vaults into a single product. Each underlying vault is itself a full strategy (rated under Mode A or B above). The meta-vault adds its own infrastructure layer on top.

**Step 1 — Rate each underlying vault.** Compute every underlying vault's strategy score using the appropriate mode (A or B). Call these scores `V₁, V₂, … Vₙ` with allocation weights `w₁, w₂, … wₙ` (summing to 1).

**Step 2 — Meta-vault economics.** The meta-vault's **economics** axis is the allocation-weighted average of the underlying vault strategy scores:

```
meta_economics = w₁ × V₁ + w₂ × V₂ + … + wₙ × Vₙ
```

This reflects the economic quality of the portfolio the meta-vault exposes depositors to.

**Step 3 — Meta-vault security and operations.** The meta-vault's **security** and **operations** axes are scored independently by raters (0–10) for the meta-vault's own contracts and governance — not inherited from underlying vaults.

**Step 4 — Meta-vault layer score.** Use vault weights:

```
meta_vault_score = 0.40 × meta_security + 0.40 × meta_operations + 0.20 × meta_economics
```

**Step 5 — Final meta-vault strategy score.** The underlying vaults collectively play the role of the "market" layer. The asset layer is the weighted composite of asset scores across underlying vaults. Composition follows the vault-strategy weights:

```
meta_strategy_score = 0.20 × asset_score + 0.40 × underlying_vaults_score + 0.40 × meta_vault_score
```

Where `underlying_vaults_score` is the allocation-weighted average of the underlying vaults' strategy scores, and `asset_score` is the allocation-weighted average of the asset scores across those vaults.

---

## 5. Output Scale

All scores are **0–10** numeric values (higher = safer). There is no letter-grade translation; the numeric score is the primary and only output.

For each entity the Alliance publishes:

- **Layer scores** (0–10) for each applicable layer.
- **Axis breakdown** (0–10) for Security, Operations, Economics within each layer.
- **Strategy score** (0–10) — the overall score for the full strategy.
- **Per-rater breakdown** — which raters contributed which axis scores (for transparency).

---

## 6. Multi-Rater Aggregation

Multiple external raters can supply scores for the same entity. The Alliance aggregates them into a single score per cell using the rules below.

### 6.1 Flexible Coverage

A rater can contribute as little as **a single axis score for a single layer** (e.g. only Asset Security). There is no requirement to cover all three axes or all layers. Each submitted axis score participates independently in the aggregation for its cell.

### 6.2 Weighted Average (Default Merge)

For each cell (layer × axis), the Alliance computes a **weighted average** of all rater scores for that cell:

```
cell_score = Σ (wᵢ × scoreᵢ) / Σ wᵢ
```

where `wᵢ` is the weight assigned to rater `i` for that cell and the sum runs over all raters who submitted a non-null score.

By default every rater has **equal weight** (wᵢ = 1 for all i, making this a simple average).

### 6.3 Adjustable Weights

The Alliance can adjust per-rater weights to reflect its assessment of rater quality, methodology alignment, or domain expertise. This includes:

- **Up-weighting** a rater whose methodology is particularly rigorous for a given layer or axis.
- **Down-weighting** a rater whose coverage is less reliable for a particular domain.
- **Dismissing** a rater entirely by setting its weight to 0.

Weight adjustments are documented, versioned alongside the methodology, and visible to users so that the influence of each rater remains transparent.

### 6.4 Null and Missing Scores

- If a rater submits `null` for an axis, that submission is excluded from the weighted average for that cell (only non-null values count).
- If **no rater** supplies a score for a given cell, **default-to-worse (0)** applies.

### 6.5 Provenance

For every entity and every scoring run, the Alliance stores which rater supplied which axis values and the weight applied to each. Users and auditors can trace every score back to its sources and verify how the weighted average was computed.

---

## 7. Transparency and Governance

- **Default-to-worse** — Missing, unverifiable, or opaque data results in the worst score (0). Opacity is a risk factor.
- **Explainability** — Scores are accompanied by the axis breakdown and per-provider contributions so that any score can be fully audited.
- **Counterparty transparency** — Every scored strategy is accompanied by a Counterparty Exposure Map (Section 8) that catalogues all protocol dependencies, their battle-testedness, and operational maturity. The map is not a scoring input; it is a context layer that helps users interpret the score.
- **Versioning** — Every computed score is tagged with `methodology_version` (e.g. v2.2). Any change to axes, weights, or rules produces a new version; historical scores remain interpretable.
- **Public methodology** — Axes, weights, and merge rules are public and open to challenge.

---

## 8. Counterparty Exposure Map

Every DeFi strategy depends on multiple protocols and external entities — from the asset issuer to the lending market, oracle provider, and vault manager. The **Counterparty Exposure Map** catalogues these dependencies so users can see exactly what they are trusting.

The map is an **informational supplement**, not a scoring input. It accompanies every scored strategy to provide context that the numeric score alone cannot convey.

### 8.1 Structure

For each strategy, every protocol or counterparty touched at any layer is recorded with the following attributes:

| Field | Description |
|-------|-------------|
| **Counterparty** | Protocol or entity name (e.g. Aave, Chainlink, Circle). |
| **Layer** | Where the exposure occurs: `asset`, `market`, or `vault`. |
| **Exposure** | `major` — the strategy's value flows directly through this counterparty. `minor` — indirect or auxiliary dependency (e.g. oracle, bridge). |
| **Lindy** | Battle-testedness tier: `High`, `Medium`, or `Low` (see 8.2). |
| **Operations** | Operational maturity tier: `High`, `Medium`, or `Low` (see 8.3). |

Example for a Morpho USDC vault deployed on Aave:

| Counterparty | Layer | Exposure | Lindy | Operations |
|--------------|-------|----------|-------|------------|
| Circle (USDC) | asset | major | High | Medium |
| Aave v3 | market | major | High | High |
| Morpho | vault | major | Medium | Medium |
| Chainlink | market | minor | High | High |

### 8.2 Lindy Score

The Lindy score reflects how battle-tested a protocol is, derived from the combination of economic value secured (TVL) and time operating without a critical exploit or loss-of-funds incident.

| Tier | Criteria |
|------|----------|
| **High** | TVL > $1 B **and** > 3 years without exploit or critical incident. |
| **Medium** | TVL > $100 M **and** > 1 year without exploit. |
| **Low** | TVL < $100 M, **or** < 1 year of operation, **or** has experienced an exploit. |

The intuition: protocols that have secured large amounts of capital over long periods without incident have demonstrated resilience. A single exploit resets the clock and drops the tier regardless of TVL.

### 8.3 Operations Level

The Operations level captures a counterparty's governance maturity and decentralization posture, sourced from **DeFiScan** or equivalent operational assessment frameworks.

| Tier | Reference | Criteria |
|------|-----------|----------|
| **High** | DeFiScan Stage 2+ or equivalent | Fully decentralized governance, immutable or long-timelock upgrades, on-chain verifiability of all parameters. |
| **Medium** | DeFiScan Stage 1 or equivalent | Partial decentralization, governance with reasonable controls (multisig + timelock), public documentation. |
| **Low** | DeFiScan Stage 0 or equivalent | Centralized control, upgradeable without meaningful timelock, limited transparency. |

When DeFiScan coverage is unavailable, the Alliance may derive the tier from equivalent public assessments or from direct inspection of governance contracts and documentation.

### 8.4 Relationship to the Score

The Counterparty Exposure Map is explicitly **not** a scoring input. The 0–10 numeric score is computed solely from the axis-weighted methodology described in Sections 3–4.

The map extends the score by providing **context**:

- A strategy rated 7/10 where every counterparty has High Lindy and High Operations signals well-understood, battle-tested risk.
- A strategy rated 7/10 where a major counterparty has Low Lindy signals emerging risk that users should weigh against the numeric score.
- Concentration of multiple `major` exposures in a single counterparty highlights single-point-of-failure risk that the aggregate score may not surface on its own.

The Alliance publishes the Counterparty Exposure Map alongside every scored entity so that users, integrators, and institutions can make fully informed decisions.

---

## Appendix: Summary of Weights

**Layer-level (axis weights):**

| Layer | Formula |
|-------|---------|
| Asset score | `0.30 × Security + 0.30 × Operations + 0.40 × Economics` |
| Market score | `0.30 × Security + 0.30 × Operations + 0.40 × Economics` |
| Vault / Meta-vault score | `0.40 × Security + 0.40 × Operations + 0.20 × Economics` |

**Strategy-level (composition modes):**

| Mode | Layers | Formula |
|------|--------|---------|
| A — Vault strategy | Asset + Market + Vault | `0.20 × Asset + 0.40 × Market + 0.40 × Vault` |
| B — Direct vault | Asset + Vault | `0.35 × Asset + 0.65 × Vault` |
| C — Market rating | Asset + Market | `0.35 × Asset + 0.65 × Market` |
| D — Meta-vault | Asset + Underlying vaults + Meta-vault | `0.20 × Asset + 0.40 × UnderlyingVaults + 0.40 × MetaVault` |
