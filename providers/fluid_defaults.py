"""Defaults rater for Fluid (Instadapp's lending and smart-vault protocol).

Fluid's security page (https://docs.fluid.io/security) lists audits by
MixBytes, StateMind, and Cantina competitions covering the lending pool,
liquidity layer, and the smart-vault collateral/debt logic. Mainnet launch:
2024-03-12.

Note: Defiscan currently maps ``fluid`` to Stage 0 (operations side). This
rater only attests *security* defaults; the merge rule will still keep
``market.operations`` unsatisfied on its own, so the overall layer stage
remains accurate.

Matches contexts whose ``vaultscan_id`` starts with ``fluid-``.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

FLUID_SECURITY = "https://docs.fluid.io/security"
FLUID_LAUNCH_DATE = "2024-03-12"


def _is_fluid(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("fluid-")


def _a(layer: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="security",
        criterion_id=cid,
        verdict="verified",
        source="fluid_defaults",
        evidence=evidence,
    )


class FluidDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "fluid_defaults"

    @property
    def organization(self) -> str | None:
        return "instadapp"

    def supported_criteria(self) -> set[str]:
        return {
            "market.security.s1.audited",
            "market.security.s1.lindy_1y",
            "vault.security.s1.audited",
            "vault.security.s1.no_critical_findings",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_fluid(ctx):
            return []
        audits = f"Fluid audit register: {FLUID_SECURITY}"
        lindy = (
            f"Fluid mainnet since {FLUID_LAUNCH_DATE}; no critical exploit on Fluid. "
            f"See {FLUID_SECURITY}"
        )
        return [
            _a("market", "market.security.s1.audited", audits),
            _a("market", "market.security.s1.lindy_1y", lindy),
            _a("vault", "vault.security.s1.audited", audits),
            _a("vault", "vault.security.s1.no_critical_findings", audits),
        ]
