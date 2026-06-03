"""Provider adapter tests with stubbed HTTP responses."""

from __future__ import annotations

from methodology import StrategyContext
from methodology.criteria import all_criterion_ids
from providers import (
    DefiPunkdRater,
    DefiscanRater,
    EulerDefaultsRater,
    FluidDefaultsRater,
    LidoDefaultsRater,
    MellowDefaultsRater,
    PharosRater,
    PhilidorRater,
    RocketPoolDefaultsRater,
    WebacyRater,
    XerberusPoolsRater,
    XerberusRater,
)


def test_supported_criteria_subset_of_registry():
    valid = all_criterion_ids()
    for rater in (
        XerberusRater(),
        PharosRater(),
        PhilidorRater(),
        WebacyRater(),
        DefiscanRater(),
        DefiPunkdRater(),
        XerberusPoolsRater(),
        LidoDefaultsRater(),
        RocketPoolDefaultsRater(),
        EulerDefaultsRater(),
        FluidDefaultsRater(),
        MellowDefaultsRater(),
    ):
        sup = rater.supported_criteria()
        assert sup, f"{rater.name} declares no criteria"
        assert sup <= valid, f"{rater.name} declares unknown criteria"


def test_defiscan_known_market_reaches_stage_one_ops():
    ctx = StrategyContext(mode="C", defiscan_market_slug="aave-v3")
    atts = DefiscanRater().attest(ctx)
    assert any(a.criterion_id == "market.operations.s1.timelock_24h" and a.verdict == "verified" for a in atts)


def test_defiscan_unknown_slug_yields_no_attestations():
    ctx = StrategyContext(mode="C", defiscan_market_slug="not-a-real-protocol")
    assert DefiscanRater().attest(ctx) == []


def test_xerberus_uses_cache_when_present():
    ctx = StrategyContext(
        mode="A",
        xerberus_asset_symbol="USDC",
        xerberus_protocol_slug="aave-v3",
    )
    ctx._cache["xerberus"] = {
        "assets": {
            "USDC": {"domain_scores": {"regulatory": 0.85, "valuation": 0.5}},
        },
        "protocols": {
            "aave-v3": {"domain_scores": {"security": 0.75, "governance": 0.45, "economics": 0.2}},
        },
    }
    atts = XerberusRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    assert ("asset.operations.s2.regulated_issuer", "verified") in by_id
    assert ("asset.strategy_economics.s1.collateral_adequate", "verified") in by_id
    assert ("market.security.s2.lindy_3y", "verified") in by_id
    assert any(
        a.criterion_id.startswith("market.strategy_economics.s1") and a.verdict == "violated"
        for a in atts
    )


def test_philidor_reads_cached_payload():
    ctx = StrategyContext(
        mode="A",
        philidor_network="ethereum",
        vault_address="0xVAULT",
    )
    ctx._cache["philidor:ethereum:0xVAULT"] = {
        "risk_vectors": {
            "platform": {"score": 9.0, "details": {"strategyScore": 6.0}},
            "control": {"score": 7.0},
        }
    }
    atts = PhilidorRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    assert ("vault.security.s2.lindy_1y", "verified") in by_id
    assert ("vault.operations.s1.timelock_24h", "verified") in by_id
    assert ("vault.strategy_economics.s1.simple_strategy", "verified") in by_id
    assert ("vault.strategy_economics.s2.proven_track_record", "verified") not in by_id


def test_webacy_high_risk_files_violation(monkeypatch):
    monkeypatch.setenv("WEBACY_API_KEY", "x")
    ctx = StrategyContext(mode="B", vault_address="0xabc0000000000000000000000000000000000000", webacy_chain="eth")
    ctx._cache["webacy:eth:0xabc0000000000000000000000000000000000000"] = {
        "risk": {"overallRisk": 90}
    }
    atts = WebacyRater().attest(ctx)
    assert atts and all(a.verdict == "violated" for a in atts)


def test_webacy_low_risk_verifies(monkeypatch):
    monkeypatch.setenv("WEBACY_API_KEY", "x")
    ctx = StrategyContext(mode="B", vault_address="0xabc0000000000000000000000000000000000000", webacy_chain="eth")
    ctx._cache["webacy:eth:0xabc0000000000000000000000000000000000000"] = {
        "risk": {"overallRisk": 5}
    }
    atts = WebacyRater().attest(ctx)
    assert atts
    assert any(a.criterion_id == "vault.security.s2.multi_audit_bounty" and a.verdict == "verified" for a in atts)


# ----- DeFiPunk'd -----------------------------------------------------------


def _defipunkd_payload(**dims):
    return {"dimensions": dims, "badge": "gold"}


def test_defipunkd_no_protocol_id_yields_nothing():
    assert DefiPunkdRater().attest(StrategyContext(mode="A")) == []


def test_defipunkd_green_grades_verify_security_and_operations():
    ctx = StrategyContext(mode="A", defipunkd_protocol_id="aave-v3")
    ctx._cache["defipunkd:aave-v3"] = _defipunkd_payload(
        verifiability="green",
        control="green",
        exit="green",
        autonomy="green",
        open_access="green",
    )
    atts = DefiPunkdRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    # Verifiability → security on both layers
    assert ("market.security.s1.audited", "verified") in by_id
    assert ("vault.security.s1.audited", "verified") in by_id
    assert ("market.security.s2.multi_audit_bounty", "verified") in by_id
    # Control + open_access on operations
    assert ("market.operations.s1.timelock_24h", "verified") in by_id
    assert ("vault.operations.s1.timelock_24h", "verified") in by_id
    assert ("vault.operations.s1.public_strategy_doc", "verified") in by_id
    # Autonomy is market-only
    assert ("market.operations.s1.quality_oracle", "verified") in by_id
    # Exit is vault-only
    assert ("vault.operations.s2.fast_withdrawal", "verified") in by_id
    # Stays out of strategy_economics entirely
    assert not any("strategy_economics" in a.criterion_id for a in atts)


def test_defipunkd_red_grade_violates_stage_one_only():
    ctx = StrategyContext(mode="A", defipunkd_protocol_id="some-cex")
    ctx._cache["defipunkd:some-cex"] = _defipunkd_payload(
        verifiability="red", control="red", exit="red",
        autonomy="red", open_access="red",
    )
    atts = DefiPunkdRater().attest(ctx)
    assert atts and all(a.verdict == "violated" for a in atts)
    # No stage-2 violations — DeFiPunk'd only flags S1 on red
    assert all(".s1." in a.criterion_id for a in atts)


def test_defipunkd_gray_emits_nothing():
    ctx = StrategyContext(mode="A", defipunkd_protocol_id="x")
    ctx._cache["defipunkd:x"] = _defipunkd_payload(
        verifiability="gray", control="gray", exit="gray",
        autonomy="gray", open_access="gray",
    )
    assert DefiPunkdRater().attest(ctx) == []


def test_defipunkd_badge_sets_weight():
    ctx = StrategyContext(mode="A", defipunkd_protocol_id="x")
    ctx._cache["defipunkd:x"] = {
        "dimensions": {"verifiability": "green"},
        "badge": "bronze",
    }
    atts = DefiPunkdRater().attest(ctx)
    assert atts
    assert all(a.weight == 0.4 for a in atts)


# ----- Xerberus pools -------------------------------------------------------


def test_xerberus_pools_no_pool_id_yields_nothing():
    assert XerberusPoolsRater().attest(StrategyContext(mode="B")) == []


def test_xerberus_pools_high_scores_verify_security_and_strategy():
    ctx = StrategyContext(mode="B", xerberus_pool_id="aave-v3-usdc-eth")
    ctx._cache["xerberus_pools:aave-v3-usdc-eth"] = {
        "pool_id": "aave-v3-usdc-eth",
        "domain_scores": {"security": 0.85, "strategy": 0.55},
        "letter_rating": "AA",
    }
    atts = XerberusPoolsRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    # security >= S2 threshold (0.7) → both S1 and S2 verified
    assert ("vault.security.s1.audited", "verified") in by_id
    assert ("vault.security.s2.multi_audit_bounty", "verified") in by_id
    # strategy in [S1, S2) → only S1 verified
    assert ("vault.strategy_economics.s1.simple_strategy", "verified") in by_id
    assert ("vault.strategy_economics.s2.proven_track_record", "verified") not in by_id
    # No operations attestations — by design
    assert not any(".operations." in a.criterion_id for a in atts)
    # No asset-layer attestations — token receipt is intentionally out of scope
    assert not any(a.layer == "asset" for a in atts)


def test_xerberus_pools_low_score_violates_stage_one():
    ctx = StrategyContext(mode="B", xerberus_pool_id="risky-pool")
    ctx._cache["xerberus_pools:risky-pool"] = {
        "domain_scores": {"security": 0.1, "strategy": 0.1},
    }
    atts = XerberusPoolsRater().attest(ctx)
    assert atts
    assert all(a.verdict == "violated" and ".s1." in a.criterion_id for a in atts)


def test_xerberus_pools_shares_organization_with_xerberus():
    # Engine COI filter treats both raters as the same organisation.
    assert XerberusPoolsRater().organization == "xerberus"


# ----- Protocol defaults (Lido, RP, Euler, Fluid, Mellow) -------------------


def test_lido_defaults_match_only_lido_prefix():
    assert LidoDefaultsRater().attest(StrategyContext(mode="B")) == []
    assert LidoDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="aave-usdc")) == []
    atts = LidoDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="lido-wsteth"))
    assert atts
    by_id = {a.criterion_id for a in atts}
    # Hits both market and vault layers + reaches Stage 2 on both
    assert "market.security.s1.audited" in by_id
    assert "market.security.s2.lindy_3y" in by_id
    assert "vault.security.s2.lindy_1y" in by_id
    assert all(a.verdict == "verified" and a.component == "security" for a in atts)


def test_rocketpool_defaults_accept_rp_alias():
    atts1 = RocketPoolDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="rocketpool-reth"))
    atts2 = RocketPoolDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="rp-reth"))
    assert atts1 and atts2
    assert {a.criterion_id for a in atts1} == {a.criterion_id for a in atts2}


def test_euler_defaults_skip_lindy_3y():
    atts = EulerDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="euler-evk-usdc"))
    by_id = {a.criterion_id for a in atts}
    assert "market.security.s1.lindy_1y" in by_id
    assert "market.security.s2.lindy_3y" not in by_id  # v2 is too young + v1 hack history


def test_fluid_defaults_only_s1_security():
    atts = FluidDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="fluid-usdc"))
    by_id = {a.criterion_id for a in atts}
    assert "market.security.s1.audited" in by_id
    # No s2 attestations — conservative on bug-bounty / multi-audit claim
    assert not any(".s2." in cid for cid in by_id)


def test_mellow_defaults_omit_no_critical_findings_per_curator():
    atts = MellowDefaultsRater().attest(StrategyContext(mode="B", vaultscan_id="mellow-re7-lrt"))
    by_id = {a.criterion_id for a in atts}
    assert "vault.security.s1.audited" in by_id
    # Curator-specific claim is intentionally NOT made by framework defaults
    assert "vault.security.s1.no_critical_findings" not in by_id


def test_defiscan_new_protocol_slugs_are_recognised():
    rater = DefiscanRater()
    for slug, expected_stage in (
        ("lido", 1), ("rocketpool", 1), ("euler-v2", 1), ("mellow", 1),
    ):
        ctx = StrategyContext(mode="C", defiscan_market_slug=slug)
        atts = rater.attest(ctx)
        assert atts, f"defiscan missed {slug}"
        if expected_stage >= 1:
            assert any(
                a.criterion_id == "market.operations.s1.timelock_24h" and a.verdict == "verified"
                for a in atts
            ), slug


def test_defiscan_new_vault_slugs_are_recognised():
    rater = DefiscanRater()
    for slug in ("lido-wsteth", "rocketpool-reth", "euler-evk-vault", "mellow-vault"):
        ctx = StrategyContext(mode="B", defiscan_vault_slug=slug)
        atts = rater.attest(ctx)
        assert any(
            a.criterion_id == "vault.operations.s1.timelock_24h" and a.verdict == "verified"
            for a in atts
        ), slug
    # Fluid-vault is explicitly Stage 0 in the curated map → files a violation
    ctx = StrategyContext(mode="B", defiscan_vault_slug="fluid-vault")
    atts = rater.attest(ctx)
    assert any(a.verdict == "violated" for a in atts)
