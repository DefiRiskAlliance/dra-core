"""Defaults rater for Mellow (Symbiotic restaking + LRT vault framework).

The Mellow vault framework is audited (https://docs.mellow.finance/security)
by ChainSecurity, Statemind, and others. Mainnet launch: 2024-04-15.

**Important — curator caveat.** Mellow vaults are operated by independent
curators (Re7, MEV Capital, Steakhouse, P2P, and others). This rater attests
*framework-level* defaults that follow from the audited Mellow base contracts
that every curator inherits, plus a handful of factually-public asset and
operations claims. Per-curator vault behaviour (strategy quality, withdrawal
queue posture, asset selection) is **not** covered here — those must come
from per-vault raters (Vaultscan, Philidor) or manual attestations. In
particular this rater does NOT attest:

- ``vault.security.s1.no_critical_findings`` — curator-specific.
- ``vault.strategy_economics.s1.simple_strategy`` — restaking with operator
  selection is not a simple single-asset deployment.
- ``asset.strategy_economics.s1.peg_or_market_stable_12m`` — LRT wrapper
  tokens are typically too young and too small to meet the criterion.

Matches contexts whose ``vaultscan_id`` starts with ``mellow-``.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

MELLOW_SECURITY = "https://docs.mellow.finance/security"
MELLOW_DOCS = "https://docs.mellow.finance/"
MELLOW_LAUNCH_DATE = "2024-04-15"


def _is_mellow(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("mellow-")


def _a(layer: str, component: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict="verified",
        source="mellow_defaults",
        evidence=evidence,
    )


_SUPPORTED = {
    # Asset (LRT wrapper) — conservative
    "asset.security.s1.audited",
    "asset.security.s1.no_recent_exploit",
    "asset.operations.s1.public_docs",
    "asset.strategy_economics.s1.collateral_adequate",
    # Market
    "market.security.s1.audited",
    "market.security.s1.lindy_1y",
    # Vault (framework-level)
    "vault.security.s1.audited",
    "vault.operations.s1.public_strategy_doc",
    "vault.strategy_economics.s1.curator_accountable",
}


class MellowDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "mellow_defaults"

    @property
    def organization(self) -> str | None:
        return "mellow"

    def supported_criteria(self) -> set[str]:
        return set(_SUPPORTED)

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_mellow(ctx):
            return []
        audits = f"Mellow vault framework audit register: {MELLOW_SECURITY}"
        lindy = (
            f"Mellow framework live since {MELLOW_LAUNCH_DATE}; "
            f"no critical framework-level exploit. See {MELLOW_SECURITY}"
        )
        return [
            # --- Asset ---
            _a("asset", "security", "asset.security.s1.audited", audits),
            _a("asset", "security", "asset.security.s1.no_recent_exploit", lindy),
            _a("asset", "operations", "asset.operations.s1.public_docs", f"Mellow docs: {MELLOW_DOCS}"),
            _a(
                "asset",
                "strategy_economics",
                "asset.strategy_economics.s1.collateral_adequate",
                "LRT wrapper is 1:1 backed by deposited ETH / LST collateral routed to "
                "Symbiotic restaking. Backing is on-chain; depositors bear restaking "
                "slashing risk on top of base staking risk.",
            ),
            # --- Market (kept) ---
            _a("market", "security", "market.security.s1.audited", audits),
            _a("market", "security", "market.security.s1.lindy_1y", lindy),
            # --- Vault (framework-level) ---
            _a("vault", "security", "vault.security.s1.audited", audits),
            _a(
                "vault",
                "operations",
                "vault.operations.s1.public_strategy_doc",
                "Mellow framework requires per-vault curator disclosures. See "
                f"{MELLOW_DOCS}",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.curator_accountable",
                "Mellow vaults publish their curator identity (e.g. Re7, MEV Capital, "
                f"Steakhouse) with public risk-reporting cadence. See {MELLOW_DOCS}",
            ),
        ]
