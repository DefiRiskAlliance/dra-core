"""Xerberus pool-level risk ratings -> vault security + strategy attestations.

Xerberus's public Risk API (``app.xerberus.io/api``) documents per-asset letter
ratings; the ``/risk/pools`` view is in beta and not yet covered by the public
docs. This rater therefore reads pool data from ``ctx._cache`` so it composes
with whatever fetch path the operator already has (cached JSON, authenticated
proxy, manual upload).

Scope per request: this rater focuses on **security and strategy** for the
vault layer only. The asset-issuer / "token receipt" angle is already covered
by the dendrogram-based :class:`XerberusRater` and intentionally not duplicated
here.

Expected cache shape, keyed ``xerberus_pools:<pool_id>``::

    {
        "pool_id": "aave-v3-usdc-ethereum",
        "domain_scores": {
            "security": 0.78,      # 0..1, higher = safer
            "strategy": 0.62,
        },
        "letter_rating": "AA",     # optional, used for evidence string
    }

Either ``domain_scores`` keys may be missing; the corresponding component is
left unattested.
"""

from __future__ import annotations

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

XERBERUS_POOLS_URL_TEMPLATE = "https://app.xerberus.io/api/risk/pools/{pool_id}"

# 0..1 scale, mirrors the existing dendrogram-based rater for consistency.
S1_THRESHOLD = 0.4
S2_THRESHOLD = 0.7

VAULT_SEC_S1 = ("vault.security.s1.audited", "vault.security.s1.no_critical_findings")
VAULT_SEC_S2 = ("vault.security.s2.multi_audit_bounty", "vault.security.s2.lindy_1y")
VAULT_ECO_S1 = (
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
)
VAULT_ECO_S2 = (
    "vault.strategy_economics.s2.proven_track_record",
    "vault.strategy_economics.s2.transparent_positions",
)


def _coerce(v: object) -> float | None:
    if v is None:
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _payload(ctx: StrategyContext, pool_id: str) -> dict | None:
    key = f"xerberus_pools:{pool_id}"
    if key in ctx._cache:
        cached = ctx._cache[key]
        return cached if isinstance(cached, dict) else None
    try:
        body = get_json(XERBERUS_POOLS_URL_TEMPLATE.format(pool_id=pool_id))
    except HttpError:
        ctx._cache[key] = None
        return None
    data = body.get("data") if isinstance(body, dict) else None
    pool = data if isinstance(data, dict) else None
    ctx._cache[key] = pool
    return pool


class XerberusPoolsRater(RaterBase):
    """Pool-level Xerberus scores, restricted to vault security + strategy."""

    @property
    def name(self) -> str:
        return "xerberus_pools"

    @property
    def organization(self) -> str | None:
        # Same organisation as the dendrogram-based XerberusRater so the
        # engine's COI filter treats them consistently.
        return "xerberus"

    def supported_criteria(self) -> set[str]:
        return {
            *VAULT_SEC_S1, *VAULT_SEC_S2,
            *VAULT_ECO_S1, *VAULT_ECO_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        pool_id = (ctx.xerberus_pool_id or "").strip()
        if not pool_id:
            return []
        pool = _payload(ctx, pool_id)
        if not pool:
            return []
        ds = pool.get("domain_scores") if isinstance(pool, dict) else None
        if not isinstance(ds, dict):
            return []
        letter = pool.get("letter_rating") if isinstance(pool, dict) else None
        sec = _coerce(ds.get("security"))
        strat = _coerce(ds.get("strategy"))

        out: list[CriterionAttestation] = []
        out.extend(
            threshold_attestations(
                sec,
                layer="vault",
                component="security",
                s1_criteria=VAULT_SEC_S1,
                s2_criteria=VAULT_SEC_S2,
                s1_threshold=S1_THRESHOLD,
                s2_threshold=S2_THRESHOLD,
                source=self.name,
                evidence=f"xerberus_pools.{pool_id}.security={sec} letter={letter}",
            )
        )
        out.extend(
            threshold_attestations(
                strat,
                layer="vault",
                component="strategy_economics",
                s1_criteria=VAULT_ECO_S1,
                s2_criteria=VAULT_ECO_S2,
                s1_threshold=S1_THRESHOLD,
                s2_threshold=S2_THRESHOLD,
                source=self.name,
                evidence=f"xerberus_pools.{pool_id}.strategy={strat} letter={letter}",
            )
        )
        return out
