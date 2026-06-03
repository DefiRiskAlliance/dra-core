"""Defaults rater for Lido (stETH / wstETH).

Lido publishes an audit register at https://lido.fi/audits covering the core
staking router, withdrawal queue, oracle set, and wstETH wrapper. The protocol
has been live on Ethereum mainnet since 2020-12-18 with no critical exploit
and runs a $2M+ bug-bounty on Immunefi. wstETH (the ERC-20 wrapper used as a
vault token across DeFi) launched 2022-02-19.

This rater attests Lido's protocol- and wrapper-layer security defaults on any
context whose ``vaultscan_id`` starts with ``lido-`` (e.g. ``lido-steth``,
``lido-wsteth``). Other criteria (operations, strategy_economics) still need
other raters or manual attestations.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

LIDO_AUDIT_REGISTER = "https://lido.fi/audits"
LIDO_BUG_BOUNTY = "https://immunefi.com/bounty/lido/"
LIDO_LAUNCH_DATE = "2020-12-18"
WSTETH_LAUNCH_DATE = "2022-02-19"


def _is_lido(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("lido-")


def _a(layer: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="security",
        criterion_id=cid,
        verdict="verified",
        source="lido_defaults",
        evidence=evidence,
    )


class LidoDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "lido_defaults"

    @property
    def organization(self) -> str | None:
        return "lido"

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
        if not _is_lido(ctx):
            return []
        audits = f"Lido audit register: {LIDO_AUDIT_REGISTER}"
        bounty = f"Immunefi bug bounty (>$2M): {LIDO_BUG_BOUNTY}"
        lindy_market = (
            f"Lido core live on Ethereum since {LIDO_LAUNCH_DATE}; "
            f"no critical protocol exploit. See {LIDO_AUDIT_REGISTER}"
        )
        lindy_vault = (
            f"wstETH wrapper live since {WSTETH_LAUNCH_DATE}. See {LIDO_AUDIT_REGISTER}"
        )
        return [
            _a("market", "market.security.s1.audited", audits),
            _a("market", "market.security.s1.lindy_1y", lindy_market),
            _a("market", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("market", "market.security.s2.lindy_3y", lindy_market),
            _a("vault", "vault.security.s1.audited", audits),
            _a("vault", "vault.security.s1.no_critical_findings", audits),
            _a("vault", "vault.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a("vault", "vault.security.s2.lindy_1y", lindy_vault),
        ]
