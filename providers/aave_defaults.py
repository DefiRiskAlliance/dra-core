"""Defaults rater for Aave v3 markets.

Aave v3 has a continuously updated public audit register at
https://aave.com/security (SigmaPrime, OpenZeppelin, Trail of Bits, ABDK,
Certora, Spearbit, and others) and has been live on Ethereum mainnet
since March 16, 2022 with no critical protocol exploit. This rater
treats both facts as sufficient evidence for the market-security S1
criteria on any reserve whose ``vaultscan_id`` starts with ``aave-``.

It does not attest any other criterion — the engine still needs other
raters (or manual attestations) to clear the remaining S1 cells.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

AAVE_AUDIT_REGISTER = "https://aave.com/security"
AAVE_V3_LAUNCH_DATE = "2022-03-16"


def _is_aave_market(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("aave-")


class AaveDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "aave_defaults"

    def supported_criteria(self) -> set[str]:
        return {
            "market.security.s1.audited",
            "market.security.s1.lindy_1y",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_aave_market(ctx):
            return []
        return [
            CriterionAttestation(
                layer="market",
                component="security",
                criterion_id="market.security.s1.audited",
                verdict="verified",
                source=self.name,
                evidence=f"Aave v3 public audit register: {AAVE_AUDIT_REGISTER}",
            ),
            CriterionAttestation(
                layer="market",
                component="security",
                criterion_id="market.security.s1.lindy_1y",
                verdict="verified",
                source=self.name,
                evidence=(
                    f"Aave v3 live on Ethereum since {AAVE_V3_LAUNCH_DATE}; "
                    f"no critical protocol exploit. See {AAVE_AUDIT_REGISTER}"
                ),
            ),
        ]
