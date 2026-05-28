# Rater Integration Guide

This document explains how an external risk rater can participate in the DeFi Risk Alliance, what data to submit, and how submissions are integrated into the Alliance's scoring pipeline. The scoring methodology itself is defined in [METHODOLOGY.md](METHODOLOGY.md).

---

## Principles

- **Credibly neutral aggregation** — No single rater owns the final score. The Alliance aggregates all contributions under open, documented rules.
- **Open methodology** — Weights, formulas, and aggregation rules are public and challengeable.
- **Transparency** — Every rater's contribution is stored and exposed so that scores can be fully audited.

---

## Becoming a Rater

### Screening

The Alliance screens every prospective rater before onboarding. Screening evaluates:

- **Methodology alignment** — Does the rater's approach produce scores that map cleanly onto the Alliance's three axes (Security, Operations, Economics)?
- **Data quality** — Are scores evidence-based, reproducible, and updated at a reasonable cadence?
- **Operational reliability** — Can the rater deliver scores via a stable API or submission channel?

Raters that pass screening are onboarded and assigned a default weight of 1 (equal to all other raters). The Alliance may later adjust weights based on observed quality (see [METHODOLOGY.md](METHODOLOGY.md) Section 6.3).

### What You Cover

A rater is **not** required to cover every layer or every axis. You can contribute as little as a single axis score for a single layer (e.g. only Asset Economics) or as much as all 9 cells across Assets, Markets, and Vaults. Each submitted score participates independently in the aggregation for its cell.

At a minimum, a rater should cover at least one axis for at least one layer to be useful to the Alliance.

---

## Submission Format

For each entity you rate, submit a JSON object conforming to this schema:

```json
{
  "entity_type": "asset | market | vault",
  "entity_id": "<chain_id>:<address_or_slug>",
  "provider": "<your_rater_name>",
  "timestamp": "<ISO 8601>",
  "dimensions": {
    "security": <0-10 | null>,
    "operations": <0-10 | null>,
    "economics": <0-10 | null>
  }
}
```

**Field details:**

| Field | Description |
|-------|-------------|
| `entity_type` | One of `asset`, `market`, or `vault`. |
| `entity_id` | Unique identifier: `chain_id:token_address` for assets, `chain_id:protocol_slug:market_id` for markets, `chain_id:vault_address` for vaults. |
| `provider` | Your rater name (assigned during onboarding). |
| `timestamp` | When the scores were computed (ISO 8601). |
| `dimensions.security` | 0–10 numeric score, or `null` if you do not assess this axis for this entity. |
| `dimensions.operations` | 0–10 numeric score, or `null`. |
| `dimensions.economics` | 0–10 numeric score, or `null`. |

**Scoring scale:** 0 = worst risk, 10 = lowest observable risk. See [METHODOLOGY.md](METHODOLOGY.md) Section 3 for detailed guidance on what each axis covers per layer.

**Null handling:** Submit `null` for any axis you choose not to score. Null values are excluded from the weighted average; they do not penalize you or the entity. If you omit an axis key entirely (rather than setting it to `null`), the submission is still accepted — the missing axis is treated as not covered.

---

## What Each Axis Covers

| Axis | Assets | Markets | Vaults |
|------|--------|---------|--------|
| **Security** | Contract maturity (Lindy), bug bounty, audits | Protocol Lindy, bug bounty, audit coverage | Vault contract Lindy, bug bounty, audit status |
| **Operations** | Documentation transparency, reserves verifiability, legal compliance | Governance (timelock, multisig), oracle quality, parameter management | Governance controls (timelock, immutability), withdrawal liquidity, pause capability |
| **Economics** | Depeg risk, collateral quality, liquidity depth | Strategy riskiness, volatility exposure, liquidation risk | Strategy risk from underlying positions |

---

## Delivery Options

Choose whichever delivery method suits your infrastructure:

### Option 1 — Push to Alliance Endpoint

Submit scores by calling the Alliance's ingestion API directly:

```
POST /ingest
Content-Type: application/json
Authorization: Bearer <your_api_key>

{
  "entity_type": "vault",
  "entity_id": "1:0xabc...def",
  "provider": "your_rater_name",
  "timestamp": "2026-03-12T10:00:00Z",
  "dimensions": { "security": 7, "operations": 8, "economics": null }
}
```

The Alliance issues you an API key during onboarding. Keys are used for authentication only and do not affect scoring weights.

### Option 2 — Alliance Pulls from Your API

Expose a public or authenticated endpoint that returns scores in the schema above. The Alliance's ingestion service calls your API on a scheduled cadence. You provide:

- Base URL and endpoint path
- Response shape (must conform to the schema or be mappable)
- Authentication method (if any — API key, OAuth, etc.)
- Rate limits (if any)

### Option 3 — Adapter

If your native API produces scores in a different format (different scale, different field names, different structure), the Alliance writes a lightweight **adapter** that maps your output into the canonical schema. You provide documentation of your API and response format; the Alliance handles the translation.

---

## How Scores Are Aggregated

1. **Collect** — The Alliance gathers submissions from all onboarded raters for a given entity.
2. **Filter** — Only non-null axis scores are included. Null and missing axes are skipped.
3. **Weighted average** — For each cell (layer × axis), compute the weighted average of all rater scores. By default, all raters have equal weight. The Alliance may adjust weights to reflect rater quality or domain expertise; adjustments are documented and versioned.
4. **Layer score** — Weighted sum of the three axis scores (30/30/40 for assets and markets; 40/40/20 for vaults).
5. **Strategy score** — Weighted sum of layer scores per the applicable composition mode (see [METHODOLOGY.md](METHODOLOGY.md) Section 4.3).
6. **Output** — A canonical score (0–10 + letter grade) per entity, plus per-rater breakdown for transparency.

---

## Onboarding Checklist

| Step | Action |
|------|--------|
| 1 | Contact the Alliance to express interest in becoming a rater. |
| 2 | Provide documentation of your methodology, coverage scope (which layers/axes), and sample output. |
| 3 | Pass the screening process (methodology alignment, data quality, reliability). |
| 4 | Agree on a delivery method (push, pull, or adapter). |
| 5 | Receive your rater name and API credentials (if using push). |
| 6 | Begin submitting scores. The Alliance verifies the first batch and activates your feed. |

---

## FAQ

**Do I need to cover all 9 cells?**
No. You can cover as few as one axis for one layer. Cover what your methodology supports.

**What if my scoring scale is different (e.g. 0–100, letter grades, PD)?**
The Alliance writes an adapter to map your scale to 0–10. Provide your scale definition and we handle the conversion.

**Can my weight be changed?**
Yes. The Alliance may adjust rater weights over time based on observed quality and methodology alignment. Weight changes are versioned and transparent.

**What happens if I stop submitting?**
Your last submitted scores remain in the system until they expire (staleness policy TBD). If all rater scores for a cell expire or are absent, default-to-worse (0) applies.
