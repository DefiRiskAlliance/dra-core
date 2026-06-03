"""Defaults rater for Euler v2 / Euler Vault Kit (EVK).

After the March 2023 incident on v1, Euler relaunched as v2 with the Euler
Vault Kit — an open-source vault framework that has been audited by Cantina
(public competition), Spearbit, ChainSecurity, OmniscienceVault, and Certora
(formal verification). Public security index: https://docs.euler.finance/security.
v2 mainnet launch: 2024-08-05. As of this writing v2 has not had a critical
exploit. Bug bounty via Immunefi.

Matches contexts whose ``vaultscan_id`` starts with ``euler-``. ``lindy_3y``
is intentionally NOT attested — v2 is younger than 3 years and the v1 history
makes the longer-Lindy claim inappropriate.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

EULER_SECURITY = "https://docs.euler.finance/security"
EULER_BUG_BOUNTY = "https://immunefi.com/bounty/eulerfinance/"
EULER_V2_LAUNCH_DATE = "2024-08-05"


def _is_euler(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("euler-")


def _a(layer: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="security",
        criterion_id=cid,
        verdict="verified",
        source="euler_defaults",
        evidence=evidence,
    )


class EulerDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "euler_defaults"

    @property
    def organization(self) -> str | None:
        return "euler"

    def supported_criteria(self) -> set[str]:
        return {
            "market.security.s1.audited",
            "market.security.s1.lindy_1y",
            "market.security.s2.multi_audit_bounty",
            "vault.security.s1.audited",
            "vault.security.s1.no_critical_findings",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_euler(ctx):
            return []
        audits = f"Euler v2 / EVK audit index: {EULER_SECURITY}"
        bounty = f"Immunefi bug bounty: {EULER_BUG_BOUNTY}"
        lindy = (
            f"Euler v2 mainnet since {EULER_V2_LAUNCH_DATE}; no critical exploit on v2. "
            f"See {EULER_SECURITY}"
        )
        return [
            _a("market", "market.security.s1.audited", audits),
            _a("market", "market.security.s1.lindy_1y", lindy),
            _a("market", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("vault", "vault.security.s1.audited", audits),
            _a("vault", "vault.security.s1.no_critical_findings", audits),
        ]
