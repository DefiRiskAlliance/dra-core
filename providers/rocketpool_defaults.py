"""Defaults rater for Rocket Pool (rETH).

Rocket Pool's audit register at https://rocketpool.net/security lists Sigma
Prime, Trail of Bits, ConsenSys Diligence, and several follow-on engagements
covering the deposit pool, the node-operator minipools, and the rETH token.
Mainnet launch: 2021-11-08; withdrawals enabled with Shapella (2023-04-12).
$1M+ Immunefi bug bounty.

This rater attests Rocket Pool's protocol- and rETH-layer defaults on any
context whose ``vaultscan_id`` starts with ``rocketpool-`` (or ``rp-``). It
covers both the security shape and the asset / vault attributes that follow
from rETH being a single-asset, on-chain-backed wrapper of Rocket Pool's
distributed validator pool.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

RP_AUDIT_REGISTER = "https://rocketpool.net/security"
RP_BUG_BOUNTY = "https://immunefi.com/bounty/rocketpool/"
RP_DOCS = "https://docs.rocketpool.net/"
RP_GOVERNANCE = "https://dao.rocketpool.net/"
RP_LAUNCH_DATE = "2021-11-08"
SHAPELLA_DATE = "2023-04-12"


def _is_rp(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("rocketpool-") or vs.startswith("rp-")


def _a(layer: str, component: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict="verified",
        source="rocketpool_defaults",
        evidence=evidence,
    )


_SUPPORTED = {
    # Asset layer
    "asset.security.s1.audited",
    "asset.security.s1.no_recent_exploit",
    "asset.security.s2.lindy_3y_clean",
    "asset.security.s2.bug_bounty_active",
    "asset.operations.s1.public_docs",
    "asset.operations.s1.reserves_attested",
    "asset.operations.s2.reserves_realtime",
    "asset.operations.s2.regulated_issuer",
    "asset.strategy_economics.s1.peg_or_market_stable_12m",
    "asset.strategy_economics.s1.collateral_adequate",
    "asset.strategy_economics.s2.peg_or_market_stable_36m",
    "asset.strategy_economics.s2.deep_liquidity",
    # Market layer
    "market.security.s1.audited",
    "market.security.s1.lindy_1y",
    "market.security.s2.multi_audit_bounty",
    "market.security.s2.lindy_3y",
    # Vault layer (rETH wrapper)
    "vault.security.s1.audited",
    "vault.security.s1.no_critical_findings",
    "vault.security.s2.multi_audit_bounty",
    "vault.security.s2.lindy_1y",
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
}


class RocketPoolDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "rocketpool_defaults"

    @property
    def organization(self) -> str | None:
        return "rocketpool"

    def supported_criteria(self) -> set[str]:
        return set(_SUPPORTED)

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_rp(ctx):
            return []
        audits = f"Rocket Pool audit register: {RP_AUDIT_REGISTER}"
        bounty = f"Immunefi bug bounty (>$1M cap): {RP_BUG_BOUNTY}"
        lindy = (
            f"Rocket Pool mainnet since {RP_LAUNCH_DATE}; withdrawals enabled "
            f"with Shapella {SHAPELLA_DATE}. No critical protocol exploit. "
            f"See {RP_AUDIT_REGISTER}"
        )
        reserves = (
            "rETH is on-chain backed by Rocket Pool's distributed validator "
            "pool. Backing ratio and validator set are fully verifiable on-chain."
        )
        market_stable = (
            "rETH market cap > $1B with deep on-chain liquidity (Balancer, "
            "Curve, Uniswap, major aggregators)."
        )
        return [
            # --- Asset layer ---
            _a("asset", "security", "asset.security.s1.audited", audits),
            _a("asset", "security", "asset.security.s1.no_recent_exploit", lindy),
            _a("asset", "security", "asset.security.s2.lindy_3y_clean", lindy),
            _a("asset", "security", "asset.security.s2.bug_bounty_active", bounty),
            _a("asset", "operations", "asset.operations.s1.public_docs", f"Public docs: {RP_DOCS}"),
            _a("asset", "operations", "asset.operations.s1.reserves_attested", reserves),
            _a("asset", "operations", "asset.operations.s2.reserves_realtime", reserves),
            _a(
                "asset",
                "operations",
                "asset.operations.s2.regulated_issuer",
                "Rocket Pool is fully decentralised: no licensed issuer, governed "
                f"by the pDAO + oDAO via RPIPs. See {RP_GOVERNANCE}. Criterion permits "
                "'fully decentralised with no issuer' as a satisfying condition.",
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s1.peg_or_market_stable_12m",
                market_stable,
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s1.collateral_adequate",
                "rETH is fully decentralised and 1:1+ collateralised by the staked "
                "ETH validator set, including ~10% node-operator RPL bond as additional "
                "loss-absorbing capital.",
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s2.peg_or_market_stable_36m",
                "rETH/ETH ratio has tracked Rocket Pool's staked ETH balance since "
                f"{RP_LAUNCH_DATE} across multiple market dislocations.",
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s2.deep_liquidity",
                "Aggregate on-chain liquidity >$100M at <1% slippage across Balancer, "
                "Curve, and Uniswap pools.",
            ),
            # --- Market layer ---
            _a("market", "security", "market.security.s1.audited", audits),
            _a("market", "security", "market.security.s1.lindy_1y", lindy),
            _a("market", "security", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("market", "security", "market.security.s2.lindy_3y", lindy),
            # --- Vault layer ---
            _a("vault", "security", "vault.security.s1.audited", audits),
            _a("vault", "security", "vault.security.s1.no_critical_findings", audits),
            _a("vault", "security", "vault.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("vault", "security", "vault.security.s2.lindy_1y", lindy),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.simple_strategy",
                "rETH represents a single share of Rocket Pool's distributed ETH "
                "staking pool. Single-asset, no embedded leverage.",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.curator_accountable",
                "Rocket Pool DAO (pDAO + oDAO) is the on-chain accountable curator. "
                f"Public RPIP process; 4+ year track record. See {RP_GOVERNANCE}",
            ),
        ]
