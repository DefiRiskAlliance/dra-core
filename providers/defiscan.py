"""DeFiScan stage anchor for ``market.operations`` and ``vault.operations``.

DeFiScan publishes a 0/1/2 stage for protocols. Until a JSON ingestion
endpoint is wired, the mapping below is curated in this file (open
methodology — pull requests welcome). When ``ctx.defiscan_market_slug`` or
``ctx.defiscan_vault_slug`` matches a known entry we attest the corresponding
operations criteria; an explicit Stage 0 entry files a violation.
"""

from __future__ import annotations

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers.base import RaterBase

DEFISCAN_MARKET_STAGES: dict[str, int] = {
    "aave-v3": 1,
    "compound-v3": 1,
    "morpho-blue": 1,
    "spark": 1,
    "fluid": 0,
    # --- added 2026: per-protocol vault expansion ---
    "lido": 1,
    "rocketpool": 1,
    "euler-v2": 1,
    "mellow": 1,
}

DEFISCAN_VAULT_STAGES: dict[str, int] = {
    "morpho-vault": 1,
    "yearn-v3": 1,
    "maker-cdp": 2,
    # --- added 2026: per-protocol vault expansion ---
    "lido-wsteth": 1,
    "rocketpool-reth": 1,
    "euler-evk-vault": 1,
    "fluid-vault": 0,
    "mellow-vault": 1,
}

MARKET_OPS_S1 = ("market.operations.s1.timelock_24h", "market.operations.s1.quality_oracle")
MARKET_OPS_S2 = ("market.operations.s2.timelock_7d_or_immutable", "market.operations.s2.dual_oracle")
VAULT_OPS_S1 = ("vault.operations.s1.timelock_24h", "vault.operations.s1.public_strategy_doc")
VAULT_OPS_S2 = ("vault.operations.s2.immutable_or_long_timelock", "vault.operations.s2.fast_withdrawal")


def _stage_to_attestations(
    stage: int,
    layer: str,
    s1_ids: tuple[str, ...],
    s2_ids: tuple[str, ...],
    source: str,
    evidence: str,
) -> list[CriterionAttestation]:
    out: list[CriterionAttestation] = []
    if stage <= 0:
        for cid in s1_ids:
            out.append(_a(layer, cid, "violated", source, evidence))
        return out
    for cid in s1_ids:
        out.append(_a(layer, cid, "verified", source, evidence))
    if stage >= 2:
        for cid in s2_ids:
            out.append(_a(layer, cid, "verified", source, evidence))
    return out


def _a(layer: str, cid: str, verdict: str, source: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component="operations",
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
        evidence=evidence,
    )


class DefiscanRater(RaterBase):
    @property
    def name(self) -> str:
        return "defiscan"

    def supported_criteria(self) -> set[str]:
        return {*MARKET_OPS_S1, *MARKET_OPS_S2, *VAULT_OPS_S1, *VAULT_OPS_S2} & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        out: list[CriterionAttestation] = []
        market_slug = (ctx.defiscan_market_slug or "").strip().lower()
        if market_slug and market_slug in DEFISCAN_MARKET_STAGES:
            stage = DEFISCAN_MARKET_STAGES[market_slug]
            out.extend(
                _stage_to_attestations(
                    stage, "market", MARKET_OPS_S1, MARKET_OPS_S2,
                    self.name, f"defiscan.market.{market_slug}=stage{stage}",
                )
            )
        vault_slug = (ctx.defiscan_vault_slug or "").strip().lower()
        if vault_slug and vault_slug in DEFISCAN_VAULT_STAGES:
            stage = DEFISCAN_VAULT_STAGES[vault_slug]
            out.extend(
                _stage_to_attestations(
                    stage, "vault", VAULT_OPS_S1, VAULT_OPS_S2,
                    self.name, f"defiscan.vault.{vault_slug}=stage{stage}",
                )
            )
        return out
