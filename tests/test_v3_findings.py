"""Regression tests for the v3.0 implementation findings (sections 4.1-4.5).

Covers:
    4.1 attestation staleness
    4.2 rater conflict-of-interest filter
    4.3 manual-override audit trail + validation
    4.4 weight wired into confidence on CriterionStatus
    4.5 COMPONENT_LABELS bridges code <-> docs
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from methodology import (
    COMPONENT_LABELS,
    CRITERIA,
    DRAEngine,
    ManualOverride,
    StrategyContext,
)
from methodology.criteria import get_criterion
from methodology.merge import resolve_attestations
from methodology.types import CriterionAttestation


def _att(cid: str, verdict: str = "verified", **kw) -> CriterionAttestation:
    layer, component, _stage, _name = cid.split(".", 3)
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=kw.pop("source", "p"),
        **kw,
    )


# ----- 4.1 staleness --------------------------------------------------------


def test_fresh_attestation_satisfies():
    cid = "asset.security.s1.audited"
    statuses = resolve_attestations([_att(cid, "verified")])
    assert statuses[cid].satisfied
    assert statuses[cid].stale == []


def test_stale_verified_attestation_collapses_to_unknown():
    cid = "market.operations.s1.quality_oracle"  # 90-day window
    long_ago = datetime.now(timezone.utc) - timedelta(days=200)
    statuses = resolve_attestations([_att(cid, "verified", timestamp=long_ago)])
    assert not statuses[cid].satisfied
    assert len(statuses[cid].stale) == 1
    assert statuses[cid].verifications == []


def test_stale_violated_attestation_does_not_poison():
    """A stale violation should NOT keep poisoning the rating forever."""
    cid = "market.operations.s1.quality_oracle"
    long_ago = datetime.now(timezone.utc) - timedelta(days=200)
    fresh_verify = _att(cid, "verified")
    stale_violate = _att(cid, "violated", source="old", timestamp=long_ago)
    statuses = resolve_attestations([stale_violate, fresh_verify])
    assert statuses[cid].satisfied, "stale violation must not block a fresh verification"


def test_staleness_clock_is_overridable():
    cid = "asset.strategy_economics.s1.peg_or_market_stable_12m"  # 30-day window
    last_week = datetime.now(timezone.utc) - timedelta(days=7)
    much_later = datetime.now(timezone.utc) + timedelta(days=60)
    statuses = resolve_attestations([_att(cid, "verified", timestamp=last_week)], now=much_later)
    assert not statuses[cid].satisfied


def test_naive_timestamp_is_assumed_utc():
    """Naive datetime should not silently break the comparison."""
    cid = "asset.security.s1.audited"
    naive = datetime.utcnow()
    a = _att(cid, "verified", timestamp=naive)
    assert a.timestamp.tzinfo is timezone.utc


# ----- 4.2 conflict-of-interest filter --------------------------------------


class _SelfRater:
    name = "yearn_curation"
    organization = "yearn"

    def attest(self, ctx):
        cid = "vault.security.s1.audited"
        return [
            CriterionAttestation(
                layer="vault", component="security",
                criterion_id=cid, verdict="verified",
                source=self.name, evidence="self",
            )
        ]

    def supported_criteria(self):
        return {"vault.security.s1.audited"}


class _IndependentRater:
    name = "independent"
    organization = "indie"

    def attest(self, ctx):
        cid = "vault.security.s1.audited"
        return [
            CriterionAttestation(
                layer="vault", component="security",
                criterion_id=cid, verdict="verified",
                source=self.name, evidence="indie",
            )
        ]

    def supported_criteria(self):
        return {"vault.security.s1.audited"}


def test_rater_self_attestation_is_dropped():
    ctx = StrategyContext(mode="B", protocol_organization="yearn")
    result = DRAEngine([_SelfRater(), _IndependentRater()]).score(ctx)
    assert "yearn_curation" in result.skipped_raters
    assert result.attestations
    assert all(a.source != "yearn_curation" for a in result.attestations)


def test_rater_not_dropped_when_organizations_differ():
    ctx = StrategyContext(mode="B", protocol_organization="aave")
    result = DRAEngine([_SelfRater(), _IndependentRater()]).score(ctx)
    assert result.skipped_raters == []
    assert any(a.source == "yearn_curation" for a in result.attestations)


def test_organization_filter_is_no_op_when_unset():
    ctx = StrategyContext(mode="B")  # protocol_organization left at None
    result = DRAEngine([_SelfRater()]).score(ctx)
    assert result.skipped_raters == []


# ----- 4.3 manual-override audit trail --------------------------------------


def test_manual_override_requires_operator():
    with pytest.raises(ValueError, match="operator"):
        ManualOverride(
            layer="vault", component="security",
            criterion_id="vault.security.s1.audited",
            verdict="verified",
            operator="manual",  # forbidden token
            rationale="ok",
            rationale_ref="https://example/pr/1",
        )


def test_manual_override_requires_rationale_ref():
    with pytest.raises(ValueError, match="rationale_ref"):
        ManualOverride(
            layer="vault", component="security",
            criterion_id="vault.security.s1.audited",
            verdict="verified",
            operator="alice",
            rationale="some reason",
            rationale_ref="",
        )


def test_manual_override_writes_audit_log(tmp_path):
    log = tmp_path / "audit.jsonl"
    override = ManualOverride(
        layer="vault", component="security",
        criterion_id="vault.security.s1.audited",
        verdict="verified",
        operator="alice@example.org",
        rationale="ran on-chain verification",
        rationale_ref="https://github.com/example/repo/pull/42",
    )
    ctx = StrategyContext(mode="B", manual_overrides=[override])
    engine = DRAEngine([], manual_override_log_path=log)
    engine.score(ctx)

    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["operator"] == "alice@example.org"
    assert record["rationale_ref"] == "https://github.com/example/repo/pull/42"
    assert record["criterion_id"] == "vault.security.s1.audited"
    assert record["verdict"] == "verified"


def test_engine_rejects_manual_attestation_with_source_manual():
    bad = CriterionAttestation(
        layer="vault", component="security",
        criterion_id="vault.security.s1.audited",
        verdict="verified",
        source="manual",
        evidence="something",
    )
    ctx = StrategyContext(mode="B", manual_attestations=[bad])
    with pytest.raises(ValueError, match="accountable operator"):
        DRAEngine([]).score(ctx)


def test_engine_rejects_manual_attestation_with_empty_evidence():
    bad = CriterionAttestation(
        layer="vault", component="security",
        criterion_id="vault.security.s1.audited",
        verdict="verified",
        source="alice@example.org",
        evidence="",
    )
    ctx = StrategyContext(mode="B", manual_attestations=[bad])
    with pytest.raises(ValueError, match="evidence"):
        DRAEngine([]).score(ctx)


# ----- 4.4 weight surfaces as confidence ------------------------------------


def test_verification_weight_sums_attestation_weights():
    cid = "asset.security.s1.audited"
    atts = [
        _att(cid, "verified", weight=1.0, source="p1"),
        _att(cid, "verified", weight=2.0, source="p2"),
        _att(cid, "violated", weight=0.5, source="p3"),
    ]
    statuses = resolve_attestations(atts)
    s = statuses[cid]
    assert s.verification_weight == pytest.approx(3.0)
    assert s.violation_weight == pytest.approx(0.5)


# ----- 4.5 component labels bridge code/docs --------------------------------


def test_component_labels_cover_all_components():
    assert COMPONENT_LABELS["strategy_economics"] == "Strategy & Economics"
    # No drift: every Criterion's component has a label.
    for c in CRITERIA:
        assert c.component in COMPONENT_LABELS


def test_max_age_days_is_defined_per_criterion():
    short = get_criterion("asset.strategy_economics.s1.peg_or_market_stable_12m")
    assert short.max_age_days == 30
    yearly = get_criterion("asset.security.s2.lindy_3y_clean")
    assert yearly.max_age_days == 365
