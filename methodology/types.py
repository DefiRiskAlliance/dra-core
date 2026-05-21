"""DRA v3.0 methodology types: layers, components, stages, criteria, attestations.

This module is the single source of truth for the data model used throughout the
engine and the provider adapters. All scoring is expressed as discrete Stages
(0/1/2), never as a continuous 0-10 number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Mapping

Layer = Literal["asset", "market", "vault"]
Component = Literal["security", "operations", "strategy_economics"]
CompositionMode = Literal["A", "B", "C", "D"]
Stage = Literal[0, 1, 2]
Verdict = Literal["verified", "violated", "unknown"]

LAYERS: tuple[Layer, ...] = ("asset", "market", "vault")
COMPONENTS: tuple[Component, ...] = ("security", "operations", "strategy_economics")
STAGES: tuple[Stage, ...] = (0, 1, 2)

# Component code value -> human-readable label. Code uses snake_case, docs use
# the ampersand form ("Strategy & Economics"); this map keeps them in sync.
COMPONENT_LABELS: dict[Component, str] = {
    "security": "Security",
    "operations": "Operations",
    "strategy_economics": "Strategy & Economics",
}


@dataclass(frozen=True)
class Criterion:
    """A single, named requirement that a (layer, component) cell must meet
    in order to reach a given Stage. Criteria are monotonic: a cell at Stage N
    must satisfy every criterion at every stage ``s`` such that ``1 <= s <= N``.

    ``max_age_days`` bounds how long an attestation may be trusted before it is
    re-collected as ``unknown``. Tight windows for fast-moving signals (peg
    stability, real-time reserves); generous windows for slow-moving facts
    (Lindy, audits, governance set-ups).
    """

    id: str
    layer: Layer
    component: Component
    stage: Stage
    description: str
    max_age_days: int = 365

    def __post_init__(self) -> None:
        if self.stage not in (1, 2):
            raise ValueError(f"criteria are only defined for stage 1 or 2, got {self.stage}")
        prefix = f"{self.layer}.{self.component}.s{self.stage}."
        if not self.id.startswith(prefix):
            raise ValueError(f"criterion id {self.id!r} must start with {prefix!r}")
        if self.max_age_days <= 0:
            raise ValueError(f"max_age_days must be positive, got {self.max_age_days}")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CriterionAttestation:
    """One provider's verdict on one criterion.

    ``timestamp`` is the time the attestation was produced (defaults to ``now``
    so live raters get correct semantics automatically; historical data must
    pass an explicit timestamp). ``as_of_block`` lets on-chain raters anchor an
    attestation to a specific block for full reproducibility.
    """

    layer: Layer
    component: Component
    criterion_id: str
    verdict: Verdict
    source: str
    evidence: str = ""
    weight: float = 1.0
    timestamp: datetime = field(default_factory=_now_utc)
    as_of_block: int | None = None

    def __post_init__(self) -> None:
        if self.verdict not in ("verified", "violated", "unknown"):
            raise ValueError(f"bad verdict {self.verdict!r}")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")
        if self.timestamp.tzinfo is None:
            # Naive timestamps would silently mis-compare across DST/UTC. Assume
            # UTC at the boundary so callers don't have to think about it.
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))


@dataclass
class CriterionStatus:
    """Resolved status for one criterion after merging all attestations.

    ``verification_weight`` / ``violation_weight`` expose the sum of attestation
    weights on each side so callers can surface a confidence signal alongside
    the binary ``satisfied`` verdict. ``stale`` carries attestations that were
    dropped for being older than the criterion's ``max_age_days`` window.
    """

    criterion: Criterion
    satisfied: bool
    verifications: list[CriterionAttestation] = field(default_factory=list)
    violations: list[CriterionAttestation] = field(default_factory=list)
    stale: list[CriterionAttestation] = field(default_factory=list)

    @property
    def attestation_count(self) -> int:
        return len(self.verifications) + len(self.violations)

    @property
    def verification_weight(self) -> float:
        return sum(a.weight for a in self.verifications)

    @property
    def violation_weight(self) -> float:
        return sum(a.weight for a in self.violations)


@dataclass
class StageMatrix:
    """Per-cell stage after rollup. Missing entries default to Stage 0."""

    cells: dict[Layer, dict[Component, Stage]] = field(default_factory=lambda: _zero_cells())

    def as_flat(self) -> dict[tuple[Layer, Component], Stage]:
        return {(ly, co): self.cells[ly][co] for ly in LAYERS for co in COMPONENTS}


def _zero_cells() -> dict[Layer, dict[Component, Stage]]:
    return {ly: {co: 0 for co in COMPONENTS} for ly in LAYERS}


def matrix_from_mapping(m: Mapping[tuple[Layer, Component], Stage]) -> StageMatrix:
    cells = _zero_cells()
    for ly in LAYERS:
        for co in COMPONENTS:
            v = m.get((ly, co), 0)
            if v not in (0, 1, 2):
                raise ValueError(f"stage must be 0/1/2, got {v} for {ly}/{co}")
            cells[ly][co] = v  # type: ignore[assignment]
    return StageMatrix(cells=cells)
