"""DeFiPunk'd transparency registry -> market and vault attestations.

DeFiPunk'd grades each protocol on five DeFiScan-v2 dimensions:

* ``verifiability``  — open-source code, audit quality, post-audit review
* ``control``        — admin privileges, contract upgradability, upgrade speed
* ``exit``           — whether users can withdraw if the team disappears
* ``autonomy``       — exposure to oracles, bridges, governance
* ``open_access``    — absence of allowlists / KYC / geofencing

Each dimension is graded ``green`` / ``orange`` / ``red`` / ``gray`` (unassessed).
``verifiability`` maps to the **security** component; the other four are
**operations** signals. DeFiPunk'd does not cover strategy & economics, so this
rater stays out of that component entirely.

Provenance is exposed via the ``badge`` field (``bronze`` / ``silver`` /
``gold``), which we surface as the attestation ``weight`` so consumers can
discount LLM-quorum grades vs human-verified ones.

There is no documented public API at the time of writing — adapters provide a
payload directly via ``ctx._cache["defipunkd:<protocol_id>"]``. The shape we
expect is::

    {
        "dimensions": {
            "verifiability": "green" | "orange" | "red" | "gray",
            "control":        "green" | "orange" | "red" | "gray",
            "exit":           "green" | "orange" | "red" | "gray",
            "autonomy":       "green" | "orange" | "red" | "gray",
            "open_access":    "green" | "orange" | "red" | "gray",
        },
        "badge": "bronze" | "silver" | "gold",
    }

When the badge is missing we fall back to ``silver`` weight (LLM-consensus).
"""

from __future__ import annotations

from typing import Iterable

from methodology.criteria import all_criterion_ids, get_criterion
from methodology.entities import StrategyContext
from methodology.types import Component, CriterionAttestation, Layer
from providers.base import RaterBase

# ----- criterion mapping ----------------------------------------------------

# Verifiability -> security audited + (when green) multi-audit/bug-bounty too.
# Stage-1 criteria are emitted on green/red; stage-2 only on green.
VERIFIABILITY_S1: dict[Layer, tuple[str, ...]] = {
    "market": ("market.security.s1.audited", "market.security.s1.lindy_1y"),
    "vault": ("vault.security.s1.audited", "vault.security.s1.no_critical_findings"),
}
VERIFIABILITY_S2: dict[Layer, tuple[str, ...]] = {
    "market": ("market.security.s2.multi_audit_bounty",),
    "vault": ("vault.security.s2.multi_audit_bounty",),
}

# Operations dimensions — each DeFiPunk'd dimension maps to a focused subset
# of the operations criteria so the signal stays interpretable.
CONTROL_S1: dict[Layer, tuple[str, ...]] = {
    "market": ("market.operations.s1.timelock_24h",),
    "vault": ("vault.operations.s1.timelock_24h",),
}
CONTROL_S2: dict[Layer, tuple[str, ...]] = {
    "market": ("market.operations.s2.timelock_7d_or_immutable",),
    "vault": ("vault.operations.s2.immutable_or_long_timelock",),
}
EXIT_S2: dict[Layer, tuple[str, ...]] = {
    "vault": ("vault.operations.s2.fast_withdrawal",),
}
AUTONOMY_S1: dict[Layer, tuple[str, ...]] = {
    "market": ("market.operations.s1.quality_oracle",),
}
AUTONOMY_S2: dict[Layer, tuple[str, ...]] = {
    "market": ("market.operations.s2.dual_oracle",),
}
OPEN_ACCESS_S1: dict[Layer, tuple[str, ...]] = {
    "market": ("market.operations.s1.timelock_24h",),  # public, gated only by timelock
    "vault": ("vault.operations.s1.public_strategy_doc",),
}

BADGE_WEIGHT: dict[str, float] = {
    "gold": 1.0,
    "silver": 0.7,
    "bronze": 0.4,
}

# ----- helpers --------------------------------------------------------------


def _attest(
    layer: Layer,
    component: Component,
    cid: str,
    verdict: str,
    source: str,
    evidence: str,
    weight: float,
) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,
        component=component,
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
        evidence=evidence,
        weight=weight,
    )


def _emit_security(
    grade: str,
    layer: Layer,
    s1_ids: Iterable[str],
    s2_ids: Iterable[str],
    source: str,
    weight: float,
    evidence: str,
) -> list[CriterionAttestation]:
    out: list[CriterionAttestation] = []
    if grade == "green":
        for cid in s1_ids:
            out.append(_attest(layer, "security", cid, "verified", source, evidence, weight))
        for cid in s2_ids:
            out.append(_attest(layer, "security", cid, "verified", source, evidence, weight))
    elif grade == "red":
        for cid in s1_ids:
            out.append(_attest(layer, "security", cid, "violated", source, evidence, weight))
    # orange / gray -> no attestation (unknown)
    return out


def _emit_operations(
    grade: str,
    layer: Layer,
    s1_ids: Iterable[str],
    s2_ids: Iterable[str],
    source: str,
    weight: float,
    evidence: str,
) -> list[CriterionAttestation]:
    out: list[CriterionAttestation] = []
    if grade == "green":
        for cid in s1_ids:
            out.append(_attest(layer, "operations", cid, "verified", source, evidence, weight))
        for cid in s2_ids:
            out.append(_attest(layer, "operations", cid, "verified", source, evidence, weight))
    elif grade == "red":
        for cid in s1_ids:
            out.append(_attest(layer, "operations", cid, "violated", source, evidence, weight))
    return out


# ----- rater ----------------------------------------------------------------


class DefiPunkdRater(RaterBase):
    """Reads cached DeFiPunk'd grades from ``ctx._cache``.

    Set ``ctx.defipunkd_protocol_id`` (e.g. ``"aave-v3"``) and inject the
    payload at ``ctx._cache[f"defipunkd:{protocol_id}"]``. There is currently
    no public REST endpoint so live fetching is intentionally not attempted.
    """

    @property
    def name(self) -> str:
        return "defipunkd"

    @property
    def organization(self) -> str | None:
        return "defipunkd"

    def supported_criteria(self) -> set[str]:
        ids: set[str] = set()
        for table in (
            VERIFIABILITY_S1, VERIFIABILITY_S2,
            CONTROL_S1, CONTROL_S2, EXIT_S2,
            AUTONOMY_S1, AUTONOMY_S2,
            OPEN_ACCESS_S1,
        ):
            for tup in table.values():
                ids.update(tup)
        return ids & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        pid = (ctx.defipunkd_protocol_id or "").strip()
        if not pid:
            return []
        payload = ctx._cache.get(f"defipunkd:{pid}")
        if not isinstance(payload, dict):
            return []
        dims = payload.get("dimensions") or {}
        if not isinstance(dims, dict):
            return []
        badge = (payload.get("badge") or "silver").strip().lower()
        weight = BADGE_WEIGHT.get(badge, 0.7)

        out: list[CriterionAttestation] = []
        verifiability = _grade(dims.get("verifiability"))
        control = _grade(dims.get("control"))
        exit_ = _grade(dims.get("exit"))
        autonomy = _grade(dims.get("autonomy"))
        open_access = _grade(dims.get("open_access"))

        for layer in ("market", "vault"):
            ev = f"defipunkd.{pid}.{layer} verifiability={verifiability}"
            out.extend(
                _emit_security(
                    verifiability, layer,  # type: ignore[arg-type]
                    VERIFIABILITY_S1.get(layer, ()),
                    VERIFIABILITY_S2.get(layer, ()),
                    self.name, weight, ev,
                )
            )
            ev = f"defipunkd.{pid}.{layer} control={control}"
            out.extend(
                _emit_operations(
                    control, layer,  # type: ignore[arg-type]
                    CONTROL_S1.get(layer, ()),
                    CONTROL_S2.get(layer, ()),
                    self.name, weight, ev,
                )
            )
            ev = f"defipunkd.{pid}.{layer} open_access={open_access}"
            out.extend(
                _emit_operations(
                    open_access, layer,  # type: ignore[arg-type]
                    OPEN_ACCESS_S1.get(layer, ()),
                    (),
                    self.name, weight, ev,
                )
            )

        # Autonomy = oracle dependence — only meaningful for markets.
        ev = f"defipunkd.{pid}.market autonomy={autonomy}"
        out.extend(
            _emit_operations(
                autonomy, "market",
                AUTONOMY_S1.get("market", ()),
                AUTONOMY_S2.get("market", ()),
                self.name, weight, ev,
            )
        )

        # Exit = withdrawal liquidity — only meaningful for vaults.
        ev = f"defipunkd.{pid}.vault exit={exit_}"
        out.extend(
            _emit_operations(
                exit_, "vault",
                (),
                EXIT_S2.get("vault", ()),
                self.name, weight, ev,
            )
        )

        # Sanity: every emitted criterion id must register on the right (layer, component).
        for a in out:
            crit = get_criterion(a.criterion_id)
            assert crit.layer == a.layer and crit.component == a.component, (
                f"defipunkd mis-mapped {a.criterion_id!r} -> {a.layer}/{a.component}"
            )
        return out


def _grade(v: object) -> str:
    if not isinstance(v, str):
        return "gray"
    g = v.strip().lower()
    if g in ("green", "orange", "red", "gray", "grey"):
        return "gray" if g == "grey" else g
    return "gray"
