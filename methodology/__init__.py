"""DeFi Risk Alliance methodology v3.0 — Stage 0/1/2 scoring."""

from .compose import applicable_layers, build_matrix, component_stage, layer_stage, strategy_stage
from .criteria import (
    CRITERIA,
    all_criterion_ids,
    assert_registry_well_formed,
    criteria_for,
    get_criterion,
)
from .engine import DRAEngine, DRAResult, Rater
from .entities import ManualOverride, StrategyContext
from .merge import resolve_attestations
from .types import (
    COMPONENT_LABELS,
    COMPONENTS,
    LAYERS,
    STAGES,
    Component,
    CompositionMode,
    Criterion,
    CriterionAttestation,
    CriterionStatus,
    Layer,
    Stage,
    StageMatrix,
    Verdict,
    matrix_from_mapping,
)

__all__ = [
    "COMPONENT_LABELS",
    "COMPONENTS",
    "CRITERIA",
    "Component",
    "CompositionMode",
    "Criterion",
    "CriterionAttestation",
    "CriterionStatus",
    "DRAEngine",
    "DRAResult",
    "LAYERS",
    "Layer",
    "ManualOverride",
    "Rater",
    "STAGES",
    "Stage",
    "StageMatrix",
    "StrategyContext",
    "Verdict",
    "all_criterion_ids",
    "applicable_layers",
    "assert_registry_well_formed",
    "build_matrix",
    "component_stage",
    "criteria_for",
    "get_criterion",
    "layer_stage",
    "matrix_from_mapping",
    "resolve_attestations",
    "strategy_stage",
]

__version__ = "3.0.0"
