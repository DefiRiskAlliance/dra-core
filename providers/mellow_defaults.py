"""Defaults rater for Mellow (Symbiotic restaking + LRT vault framework).

The Mellow vault framework is audited (https://docs.mellow.finance/security)
by ChainSecurity, Statemind, and others. Mainnet launch: 2024-04-15.

**Important — curator caveat.** Mellow vaults are operated by independent
curators (Re7, MEV Capital, Steakhouse, P2P, and others). This rater only
attests *framework-level* security defaults — the audited Mellow base
contracts that every curator inherits. Per-curator vault behaviour (strategy
quality, withdrawal queue posture, asset selection) is **not** covered here
and must come from per-vault raters (Vaultscan, Philidor) or manual
attestations. In particular this rater does NOT attest
``vault.security.s1.no_critical_findings`` since that's a curator-specific
claim.

Matches contexts whose ``vaultscan_id`` starts with ``mellow-``.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

MELLOW_SECURITY = "https://docs.mellow.finance/security"
MELLOW_LAUNCH_DATE = "2024-04-15"


def _is_mellow(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("mellow-")


def _a(layer: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="security",
        criterion_id=cid,
        verdict="verified",
        source="mellow_defaults",
        evidence=evidence,
    )


class MellowDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "mellow_defaults"

    @property
    def organization(self) -> str | None:
        return "mellow"

    def supported_criteria(self) -> set[str]:
        return {
            "market.security.s1.audited",
            "market.security.s1.lindy_1y",
            "vault.security.s1.audited",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_mellow(ctx):
            return []
        audits = f"Mellow vault framework audit register: {MELLOW_SECURITY}"
        lindy = (
            f"Mellow framework live since {MELLOW_LAUNCH_DATE}; "
            f"no critical framework-level exploit. See {MELLOW_SECURITY}"
        )
        return [
            _a("market", "market.security.s1.audited", audits),
            _a("market", "market.security.s1.lindy_1y", lindy),
            _a("vault", "vault.security.s1.audited", audits),
        ]
