"""Strategy context and manual-override schema passed to the DRA engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import Component, CompositionMode, CriterionAttestation, Layer, Verdict


_FORBIDDEN_OPERATOR_TOKENS = {"", "manual", "manual override", "operator"}


@dataclass
class ManualOverride:
    """A reviewer-supplied attestation that bypasses automated raters.

    Every override must carry an accountable operator identity and a public
    rationale reference (PR, issue, doc link). The engine refuses anonymous
    overrides and appends each one to a JSONL audit log when configured.
    """

    layer: Layer
    component: Component
    criterion_id: str
    verdict: Verdict
    operator: str
    rationale: str
    rationale_ref: str

    def __post_init__(self) -> None:
        op = (self.operator or "").strip()
        if op.lower() in _FORBIDDEN_OPERATOR_TOKENS:
            raise ValueError(
                "ManualOverride.operator must be a real, accountable identity "
                "(not empty, not 'manual')"
            )
        if not (self.rationale or "").strip():
            raise ValueError("ManualOverride.rationale is required")
        if not (self.rationale_ref or "").strip():
            raise ValueError(
                "ManualOverride.rationale_ref must point at a PR, issue, or doc"
            )
        if self.verdict not in ("verified", "violated", "unknown"):
            raise ValueError(f"bad verdict {self.verdict!r}")


@dataclass
class StrategyContext:
    """All identifiers and overrides a provider may need to attest criteria.

    The engine never inspects most of these fields directly — they are passed
    through to provider adapters which look up the bits they care about.
    """

    methodology_version: str = "v3.0"
    mode: CompositionMode = "A"

    protocol_organization: str | None = None
    """Slug of the organisation that runs the rated protocol/vault. When a
    rater declares the same ``organization``, the engine drops its attestations
    to keep the rating credibly neutral (DRA v3.0 §4.2)."""

    asset_is_stablecoin: bool = True
    xerberus_asset_symbol: str = ""
    pharos_stablecoin_id: str | None = None

    xerberus_protocol_slug: str | None = None
    defiscan_market_slug: str | None = None
    defiscan_vault_slug: str | None = None

    philidor_network: str | None = None
    vault_address: str | None = None
    webacy_chain: str | None = None

    staking_rewards_name_substr: str | None = None
    staking_rewards_chain: str | None = None

    yearn_curation_report_url: str | None = None

    vaultscan_id: str | None = None

    philidor_fill_market_from_vault: bool = False

    manual_attestations: list[CriterionAttestation] = field(default_factory=list)
    """Reviewer-supplied attestations that bypass automated providers. Each
    must carry a non-empty ``source`` (operator identity) and non-empty
    ``evidence`` (rationale with PR/issue link) or the engine refuses to score.
    """

    manual_overrides: list[ManualOverride] = field(default_factory=list)
    """Structured manual overrides — preferred over ``manual_attestations`` for
    review-time changes because the schema enforces operator + rationale_ref."""

    _cache: dict[str, Any] = field(default_factory=dict, repr=False)
