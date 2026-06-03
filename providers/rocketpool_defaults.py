"""Defaults rater for Rocket Pool (rETH).

Rocket Pool's audit register at https://rocketpool.net/security lists Sigma
Prime, Trail of Bits, ConsenSys Diligence, and several follow-on engagements
covering the deposit pool, the node-operator minipools, and the rETH token.
Mainnet launch: 2021-11-08; withdrawals enabled with Shapella (2023-04-12).
$1M+ Immunefi bug bounty.

Matches contexts whose ``vaultscan_id`` starts with ``rocketpool-`` (e.g.
``rocketpool-reth``).
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

RP_AUDIT_REGISTER = "https://rocketpool.net/security"
RP_BUG_BOUNTY = "https://immunefi.com/bounty/rocketpool/"
RP_LAUNCH_DATE = "2021-11-08"


def _is_rp(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("rocketpool-") or vs.startswith("rp-")


def _a(layer: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="security",
        criterion_id=cid,
        verdict="verified",
        source="rocketpool_defaults",
        evidence=evidence,
    )


class RocketPoolDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "rocketpool_defaults"

    @property
    def organization(self) -> str | None:
        return "rocketpool"

    def supported_criteria(self) -> set[str]:
        return {
            "market.security.s1.audited",
            "market.security.s1.lindy_1y",
            "market.security.s2.multi_audit_bounty",
            "market.security.s2.lindy_3y",
            "vault.security.s1.audited",
            "vault.security.s1.no_critical_findings",
            "vault.security.s2.multi_audit_bounty",
            "vault.security.s2.lindy_1y",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_rp(ctx):
            return []
        audits = f"Rocket Pool audit register: {RP_AUDIT_REGISTER}"
        bounty = f"Immunefi bug bounty (>$1M): {RP_BUG_BOUNTY}"
        lindy = (
            f"Rocket Pool mainnet since {RP_LAUNCH_DATE}; no critical exploit. "
            f"See {RP_AUDIT_REGISTER}"
        )
        return [
            _a("market", "market.security.s1.audited", audits),
            _a("market", "market.security.s1.lindy_1y", lindy),
            _a("market", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("market", "market.security.s2.lindy_3y", lindy),
            _a("vault", "vault.security.s1.audited", audits),
            _a("vault", "vault.security.s1.no_critical_findings", audits),
            _a("vault", "vault.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("vault", "vault.security.s2.lindy_1y", lindy),
        ]
