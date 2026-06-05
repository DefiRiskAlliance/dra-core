"""Defaults rater for Euler v2 / Euler Vault Kit (EVK).

After the March 2023 incident on v1, Euler relaunched as v2 with the Euler
Vault Kit — an open-source vault framework that has been audited by Cantina
(public competition), Spearbit, ChainSecurity, OmniscienceVault, and Certora
(formal verification). Public security index: https://docs.euler.finance/security.
v2 mainnet launch: 2024-08-05. As of this writing v2 has not had a critical
exploit. Bug bounty via Immunefi.

Matches contexts whose ``vaultscan_id`` starts with ``euler-``. ``lindy_3y``
is intentionally NOT attested — v2 is younger than 3 years and the v1 history
makes the longer-Lindy claim inappropriate. Asset-layer attestations are
deliberately skipped — the asset is whatever the depositor holds (USDC, WETH,
etc.), not Euler-specific.
"""

from __future__ import annotations

from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

EULER_SECURITY = "https://docs.euler.finance/security"
EULER_BUG_BOUNTY = "https://immunefi.com/bounty/eulerfinance/"
EULER_DOCS = "https://docs.euler.finance/"
EULER_GOVERNANCE = "https://forum.euler.finance/"
EULER_V2_LAUNCH_DATE = "2024-08-05"


def _is_euler(ctx: StrategyContext) -> bool:
    vs = (ctx.vaultscan_id or "").lower()
    return vs.startswith("euler-")


def _a(layer: str, component: str, cid: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict="verified",
        source="euler_defaults",
        evidence=evidence,
    )


_SUPPORTED = {
    # Market layer
    "market.security.s1.audited",
    "market.security.s1.lindy_1y",
    "market.security.s2.multi_audit_bounty",
    "market.strategy_economics.s1.conservative_params",
    "market.strategy_economics.s1.healthy_utilization",
    # Vault layer (Euler vaults built on EVK)
    "vault.security.s1.audited",
    "vault.security.s1.no_critical_findings",
    "vault.operations.s1.public_strategy_doc",
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
}


class EulerDefaultsRater(RaterBase):
    @property
    def name(self) -> str:
        return "euler_defaults"

    @property
    def organization(self) -> str | None:
        return "euler"

    def supported_criteria(self) -> set[str]:
        return set(_SUPPORTED)

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not _is_euler(ctx):
            return []
        audits = f"Euler v2 / EVK audit index: {EULER_SECURITY}"
        bounty = f"Immunefi bug bounty: {EULER_BUG_BOUNTY}"
        lindy = (
            f"Euler v2 mainnet since {EULER_V2_LAUNCH_DATE}; no critical exploit "
            f"on v2. See {EULER_SECURITY}"
        )
        prime_disclaimer = (
            "Euler 'Prime' vaults are the Euler DAO's conservative reference "
            "vaults: blue-chip collateral, governance-set LTV / liquidation "
            "thresholds, and explicit borrow caps. Per-vault parameters published "
            f"at {EULER_DOCS}"
        )
        return [
            # --- Market ---
            _a("market", "security", "market.security.s1.audited", audits),
            _a("market", "security", "market.security.s1.lindy_1y", lindy),
            _a("market", "security", "market.security.s2.multi_audit_bounty", f"{audits}; {bounty}"),
            _a(
                "market",
                "strategy_economics",
                "market.strategy_economics.s1.conservative_params",
                prime_disclaimer,
            ),
            _a(
                "market",
                "strategy_economics",
                "market.strategy_economics.s1.healthy_utilization",
                "EVK enforces per-vault supply and borrow caps; Prime vaults are "
                "governance-tuned to keep utilisation below saturation. Live "
                f"parameters at {EULER_DOCS}",
            ),
            # --- Vault ---
            _a("vault", "security", "vault.security.s1.audited", audits),
            _a("vault", "security", "vault.security.s1.no_critical_findings", audits),
            _a(
                "vault",
                "operations",
                "vault.operations.s1.public_strategy_doc",
                f"Public Euler docs and Prime vault parameters: {EULER_DOCS}",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.simple_strategy",
                "Euler Prime vaults supply a single asset to a single EVK market. "
                "No embedded leverage; collateral and debt are isolated per vault.",
            ),
            _a(
                "vault",
                "strategy_economics",
                "vault.strategy_economics.s1.curator_accountable",
                "Euler DAO is the on-chain curator for Prime vaults via on-chain "
                f"governance. Discussion: {EULER_GOVERNANCE}",
            ),
        ]
