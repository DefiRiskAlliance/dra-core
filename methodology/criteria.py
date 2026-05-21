"""DRA v3.0 criteria registry — the open, versioned rubric.

Every (layer, component) pair has at least one Stage 1 criterion and at least
one Stage 2 criterion. Stages are monotonic: a cell reaches Stage N only if
every criterion at every stage 1..N is satisfied.

This file is the single authoritative source — provider adapters MUST refer to
these criterion ids by string. Tests verify well-formedness.
"""

from __future__ import annotations

from .types import COMPONENTS, LAYERS, Component, Criterion, Layer, Stage

CRITERIA: tuple[Criterion, ...] = (
    # --- ASSET × SECURITY ---
    Criterion(
        id="asset.security.s1.audited",
        layer="asset",
        component="security",
        stage=1,
        description="Token contract audited within the last 24 months by a reputable firm.",
    ),
    Criterion(
        id="asset.security.s1.no_recent_exploit",
        layer="asset",
        component="security",
        stage=1,
        description="No critical exploit affecting the token contract in the last 12 months.",
        max_age_days=180,
    ),
    Criterion(
        id="asset.security.s2.lindy_3y_clean",
        layer="asset",
        component="security",
        stage=2,
        description="Token contract live for at least 3 years with no critical incident.",
    ),
    Criterion(
        id="asset.security.s2.bug_bounty_active",
        layer="asset",
        component="security",
        stage=2,
        description="Active, well-funded bug bounty program (>= $500k payout cap).",
    ),
    # --- ASSET × OPERATIONS ---
    Criterion(
        id="asset.operations.s1.public_docs",
        layer="asset",
        component="operations",
        stage=1,
        description="Public documentation, identified issuer, and clearly stated user rights.",
    ),
    Criterion(
        id="asset.operations.s1.reserves_attested",
        layer="asset",
        component="operations",
        stage=1,
        description="Reserves attested at least quarterly by an independent auditor (or fully on-chain collateral).",
        max_age_days=120,
    ),
    Criterion(
        id="asset.operations.s2.reserves_realtime",
        layer="asset",
        component="operations",
        stage=2,
        description="Daily or real-time proof of reserves with full asset-level breakdown.",
        max_age_days=30,
    ),
    Criterion(
        id="asset.operations.s2.regulated_issuer",
        layer="asset",
        component="operations",
        stage=2,
        description="Issuer holds a recognised license in a major jurisdiction (or asset is fully decentralised with no issuer).",
    ),
    # --- ASSET × STRATEGY ECONOMICS ---
    Criterion(
        id="asset.strategy_economics.s1.peg_or_market_stable_12m",
        layer="asset",
        component="strategy_economics",
        stage=1,
        description="For stables: max peg deviation < 1% over the last 12 months. For non-stables: market cap > $100M and active multi-venue liquidity.",
        max_age_days=30,
    ),
    Criterion(
        id="asset.strategy_economics.s1.collateral_adequate",
        layer="asset",
        component="strategy_economics",
        stage=1,
        description="Asset is fully collateralised (cash-equivalent reserves) or fully decentralised with overcollateralisation.",
        max_age_days=90,
    ),
    Criterion(
        id="asset.strategy_economics.s2.peg_or_market_stable_36m",
        layer="asset",
        component="strategy_economics",
        stage=2,
        description="Peg/economic resilience demonstrated through at least 3 years and one major market dislocation.",
        max_age_days=90,
    ),
    Criterion(
        id="asset.strategy_economics.s2.deep_liquidity",
        layer="asset",
        component="strategy_economics",
        stage=2,
        description="Deep on-chain liquidity (>$50M depth at <1% slippage) across multiple independent venues.",
        max_age_days=30,
    ),
    # --- MARKET × SECURITY ---
    Criterion(
        id="market.security.s1.audited",
        layer="market",
        component="security",
        stage=1,
        description="Protocol audited by at least one reputable firm; no unresolved critical findings.",
    ),
    Criterion(
        id="market.security.s1.lindy_1y",
        layer="market",
        component="security",
        stage=1,
        description="Protocol live at least 1 year without a critical exploit.",
    ),
    Criterion(
        id="market.security.s2.multi_audit_bounty",
        layer="market",
        component="security",
        stage=2,
        description="At least 2 independent audits and an active bug bounty program.",
    ),
    Criterion(
        id="market.security.s2.lindy_3y",
        layer="market",
        component="security",
        stage=2,
        description="Protocol live at least 3 years without a critical exploit.",
    ),
    # --- MARKET × OPERATIONS ---
    Criterion(
        id="market.operations.s1.timelock_24h",
        layer="market",
        component="operations",
        stage=1,
        description="Privileged operations are gated by a >= 24h timelock.",
    ),
    Criterion(
        id="market.operations.s1.quality_oracle",
        layer="market",
        component="operations",
        stage=1,
        description="Price feeds use a tier-1 oracle (Chainlink, RedStone, Pyth, or equivalent).",
        max_age_days=90,
    ),
    Criterion(
        id="market.operations.s2.timelock_7d_or_immutable",
        layer="market",
        component="operations",
        stage=2,
        description="Core contracts immutable, or privileged operations behind a >= 7d timelock with a credible multisig (>= 5/9).",
    ),
    Criterion(
        id="market.operations.s2.dual_oracle",
        layer="market",
        component="operations",
        stage=2,
        description="Dual or redundant oracle set-up with sanity checks, deviation thresholds, and fallback paths.",
        max_age_days=90,
    ),
    # --- MARKET × STRATEGY ECONOMICS ---
    Criterion(
        id="market.strategy_economics.s1.conservative_params",
        layer="market",
        component="strategy_economics",
        stage=1,
        description="LTV, liquidation thresholds, and supply/borrow caps are conservative relative to collateral volatility.",
        max_age_days=90,
    ),
    Criterion(
        id="market.strategy_economics.s1.healthy_utilization",
        layer="market",
        component="strategy_economics",
        stage=1,
        description="Utilisation managed below 95% with caps in place to prevent withdrawal failures.",
        max_age_days=30,
    ),
    Criterion(
        id="market.strategy_economics.s2.proven_under_stress",
        layer="market",
        component="strategy_economics",
        stage=2,
        description="Market has survived at least one major dislocation event without accruing bad debt.",
    ),
    Criterion(
        id="market.strategy_economics.s2.diversified_collateral",
        layer="market",
        component="strategy_economics",
        stage=2,
        description="Multi-collateral set-up with isolation modes or e-mode segregation for risky assets.",
        max_age_days=90,
    ),
    # --- VAULT × SECURITY ---
    Criterion(
        id="vault.security.s1.audited",
        layer="vault",
        component="security",
        stage=1,
        description="Vault contracts audited; no unresolved critical findings.",
    ),
    Criterion(
        id="vault.security.s1.no_critical_findings",
        layer="vault",
        component="security",
        stage=1,
        description="No outstanding critical or high-severity vulnerabilities reported by any monitor.",
        max_age_days=180,
    ),
    Criterion(
        id="vault.security.s2.multi_audit_bounty",
        layer="vault",
        component="security",
        stage=2,
        description="At least 2 independent audits and an active bug bounty.",
    ),
    Criterion(
        id="vault.security.s2.lindy_1y",
        layer="vault",
        component="security",
        stage=2,
        description="Vault live at least 1 year at non-trivial TVL with no security incident.",
    ),
    # --- VAULT × OPERATIONS ---
    Criterion(
        id="vault.operations.s1.timelock_24h",
        layer="vault",
        component="operations",
        stage=1,
        description="Privileged vault operations behind a >= 24h timelock.",
    ),
    Criterion(
        id="vault.operations.s1.public_strategy_doc",
        layer="vault",
        component="operations",
        stage=1,
        description="Strategy and curator are publicly documented; deposit/withdraw flow is transparent.",
    ),
    Criterion(
        id="vault.operations.s2.immutable_or_long_timelock",
        layer="vault",
        component="operations",
        stage=2,
        description="Vault core is immutable or behind a >= 7d timelock; depositors have a meaningful reaction window.",
    ),
    Criterion(
        id="vault.operations.s2.fast_withdrawal",
        layer="vault",
        component="operations",
        stage=2,
        description="Withdrawals are instant or settle within 24h with no caps under normal conditions.",
    ),
    # --- VAULT × STRATEGY ECONOMICS ---
    Criterion(
        id="vault.strategy_economics.s1.simple_strategy",
        layer="vault",
        component="strategy_economics",
        stage=1,
        description="Single-market or single-asset deployment with no embedded leverage.",
    ),
    Criterion(
        id="vault.strategy_economics.s1.curator_accountable",
        layer="vault",
        component="strategy_economics",
        stage=1,
        description="Identified curator with a public track record and accountability mechanism.",
    ),
    Criterion(
        id="vault.strategy_economics.s2.proven_track_record",
        layer="vault",
        component="strategy_economics",
        stage=2,
        description="At least 12 months at strategy capacity without realised loss.",
    ),
    Criterion(
        id="vault.strategy_economics.s2.transparent_positions",
        layer="vault",
        component="strategy_economics",
        stage=2,
        description="Real-time on-chain breakdown of all positions and counterparties.",
    ),
)


_BY_ID: dict[str, Criterion] = {c.id: c for c in CRITERIA}


def get_criterion(criterion_id: str) -> Criterion:
    try:
        return _BY_ID[criterion_id]
    except KeyError as exc:
        raise KeyError(f"unknown criterion id {criterion_id!r}") from exc


def criteria_for(layer: Layer, component: Component, stage: Stage | None = None) -> tuple[Criterion, ...]:
    return tuple(
        c
        for c in CRITERIA
        if c.layer == layer and c.component == component and (stage is None or c.stage == stage)
    )


def all_criterion_ids() -> set[str]:
    return set(_BY_ID.keys())


def assert_registry_well_formed() -> None:
    """Sanity check used by tests — every cell has S1 and S2 criteria, ids unique."""
    if len(_BY_ID) != len(CRITERIA):
        raise AssertionError("duplicate criterion ids")
    for ly in LAYERS:
        for co in COMPONENTS:
            for stg in (1, 2):
                if not criteria_for(ly, co, stg):  # type: ignore[arg-type]
                    raise AssertionError(f"missing stage {stg} criterion for {ly}/{co}")
