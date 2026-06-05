"""Defaults rater for Lido (stETH / wstETH).

Lido publishes an audit register at https://lido.fi/audits covering the core
staking router, withdrawal queue, oracle set, and wstETH wrapper. The protocol
has been live on Ethereum mainnet since 2020-12-18 with no critical exploit
and runs a $2M+ bug-bounty on Immunefi. wstETH (the ERC-20 wrapper used as a
vault token across DeFi) launched 2022-02-19.

This rater attests Lido's protocol- and wrapper-layer defaults on any context
whose ``vaultscan_id`` starts with ``lido-`` (e.g. ``lido-steth``,
``lido-wsteth``). It covers both the security shape and the asset / vault
attributes that follow from wstETH being a fully on-chain, single-asset
wrapper of stETH (which itself is 1:1 with deposited ETH).
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

LIDO_AUDIT_REGISTER = "https://lido.fi/audits"
LIDO_BUG_BOUNTY = "https://immunefi.com/bounty/lido/"
LIDO_DOCS = "https://docs.lido.fi/"
LIDO_GOVERNANCE = "https://snapshot.org/#/lido-snapshot.eth"
LIDO_LAUNCH_DATE = "2020-12-18"
WSTETH_LAUNCH_DATE = "2022-02-19"


def _is_lido(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("lido-")


def _a(layer: str, component: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict="verified",
        source="lido_defaults",
        evidence=evidence,
    )


_SUPPORTED = {
    # Asset layer (wstETH is the asset)
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
    # Market layer (when wstETH/stETH is used as collateral elsewhere; kept
    # for compatibility with the previous coverage shape)
    "market.security.s1.audited",
    "market.security.s1.lindy_1y",
    "market.security.s2.multi_audit_bounty",
    "market.security.s2.lindy_3y",
    # Vault layer (the wstETH wrapper as a "vault" in Mode B)
    "vault.security.s1.audited",
    "vault.security.s1.no_critical_findings",
    "vault.security.s2.multi_audit_bounty",
    "vault.security.s2.lindy_1y",
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
}


class LidoDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "lido_defaults"

    @property
    def organization(self) -> str | None:
        return "lido"

    def supported_criteria(self) -> set[str]:
        return set(_SUPPORTED)

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_lido(ctx):
            return []
        audits = f"Lido audit register: {LIDO_AUDIT_REGISTER}"
        bounty = f"Immunefi bug bounty (>$2M cap): {LIDO_BUG_BOUNTY}"
        lindy_market = (
            f"Lido core live on Ethereum since {LIDO_LAUNCH_DATE}; "
            f"no critical protocol exploit. See {LIDO_AUDIT_REGISTER}"
        )
        lindy_vault = (
            f"wstETH wrapper live since {WSTETH_LAUNCH_DATE} (>3y as of 2025). "
            f"See {LIDO_AUDIT_REGISTER}"
        )
        reserves = (
            "wstETH is 1:1 backed by stETH, which is 1:1 backed by ETH deposited "
            "into Lido validators. Backing is fully on-chain and verifiable in "
            "real time."
        )
        market_stable = (
            "wstETH market cap > $10B with deep multi-venue liquidity (Curve, "
            "Balancer, Uniswap, major CEXs)."
        )
        return [
            # --- Asset layer ---
            _a("asset", "security", "asset.security.s1.audited", audits),
            _a("asset", "security", "asset.security.s1.no_recent_exploit", lindy_vault),
            _a("asset", "security", "asset.security.s2.lindy_3y_clean", lindy_vault),
            _a("asset", "security", "asset.security.s2.bug_bounty_active", bounty),
            _a("asset", "operations", "asset.operations.s1.public_docs", f"Public docs: {LIDO_DOCS}"),
            _a("asset", "operations", "asset.operations.s1.reserves_attested", reserves),
            _a("asset", "operations", "asset.operations.s2.reserves_realtime", reserves),
            _a(
                "asset",
                "operations",
                "asset.operations.s2.regulated_issuer",
                "Lido is fully decentralised: no licensed issuer, governed on-chain by "
                f"LDO holders via {LIDO_GOVERNANCE}. Criterion permits 'fully "
                "decentralised with no issuer' as a satisfying condition.",
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
                "wstETH is fully decentralised and overcollateralised relative to stETH "
                "(1:1 with a growing stETH/wstETH ratio reflecting accrued staking yield).",
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s2.peg_or_market_stable_36m",
                "wstETH/ETH ratio has tracked stETH's mark since 2022-02 across multiple "
                "market dislocations (May 2022, FTX, March 2023 banking).",
            ),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s2.deep_liquidity",
                "Aggregate on-chain liquidity >$500M at <1% slippage across Curve, "
                "Balancer, and Uniswap pools.",
            ),
            # --- Market layer (kept for compatibility) ---
            _a("market", "security", "market.security.s1.audited", audits),
            _a("market", "security", "market.security.s1.lindy_1y", lindy_market),
            _a("market", "security", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("market", "security", "market.security.s2.lindy_3y", lindy_market),
            # --- Vault layer ---
            _a("vault", "security", "vault.security.s1.audited", audits),
            _a("vault", "security", "vault.security.s1.no_critical_findings", audits),
            _a("vault", "security", "vault.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("vault", "security", "vault.security.s2.lindy_1y", lindy_vault),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.simple_strategy",
                "wstETH is a non-rebasing 1:1 wrapper of stETH. Single-asset, no leverage.",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.curator_accountable",
                "Lido DAO is the on-chain accountable curator: LDO governance, "
                f"on-chain LIPs, and a 5+ year public track record. See {LIDO_GOVERNANCE}",
            ),
        ]
