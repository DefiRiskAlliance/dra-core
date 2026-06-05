"""Defaults rater for Fluid (Instadapp's lending and smart-vault protocol).

Fluid's security page (https://docs.fluid.instadapp.io/audits-and-security.html) lists audits by
MixBytes, StateMind, and Cantina competitions covering the lending pool,
liquidity layer, and the smart-vault collateral/debt logic. Mainnet launch:
2024-03-12.

Note: Defiscan currently maps ``fluid`` to Stage 0 on the operations side
(market.operations and vault.operations). This rater attests *security* and
*strategy_economics* defaults; operations remain a Defiscan-driven Stage 0
unless contested via a manual override or a counter-attestation. The merge
rule pessimistically keeps any cell with even one ``violated`` at 0, so the
overall layer stage stays accurate.

Matches contexts whose ``vaultscan_id`` starts with ``fluid-``.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

FLUID_SECURITY = "https://docs.fluid.instadapp.io/audits-and-security.html"
FLUID_DOCS = "https://docs.fluid.instadapp.io/"
FLUID_LAUNCH_DATE = "2024-03-12"


def _is_fluid(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("fluid-")


def _a(layer: str, component: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict="verified",
        source="fluid_defaults",
        evidence=evidence,
    )


_SUPPORTED = {
    # Market
    "market.security.s1.audited",
    "market.security.s1.lindy_1y",
    "market.strategy_economics.s1.conservative_params",
    "market.strategy_economics.s1.healthy_utilization",
    # Vault
    "vault.security.s1.audited",
    "vault.security.s1.no_critical_findings",
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
}


class FluidDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "fluid_defaults"

    @property
    def organization(self) -> str | None:
        return "instadapp"

    def supported_criteria(self) -> set[str]:
        return set(_SUPPORTED)

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_fluid(ctx):
            return []
        audits = f"Fluid audit register: {FLUID_SECURITY}"
        lindy = (
            f"Fluid mainnet since {FLUID_LAUNCH_DATE}; no critical exploit on Fluid. "
            f"See {FLUID_SECURITY}"
        )
        params = (
            "Fluid smart vaults publish per-collateral LTV and liquidation thresholds. "
            f"Live parameters at {FLUID_DOCS}"
        )
        return [
            # --- Market ---
            _a("market", "security", "market.security.s1.audited", audits),
            _a("market", "security", "market.security.s1.lindy_1y", lindy),
            _a(
                "market",
                "strategy_economics",
                "market.strategy_economics.s1.conservative_params",
                params,
            ),
            _a(
                "market",
                "strategy_economics",
                "market.strategy_economics.s1.healthy_utilization",
                "Fluid liquidity layer publishes utilisation caps per asset; current "
                f"snapshot at {FLUID_DOCS}",
            ),
            # --- Vault ---
            _a("vault", "security", "vault.security.s1.audited", audits),
            _a("vault", "security", "vault.security.s1.no_critical_findings", audits),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.simple_strategy",
                "Fluid USDC vault supplies USDC to the Fluid liquidity layer. "
                "Single asset, no embedded leverage on the supply side.",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.curator_accountable",
                "Instadapp / Fluid governance is the identified curator with a "
                f"multi-year public track record. See {FLUID_DOCS}",
            ),
        ]
