"""Stage rollup: criteria -> cell stage -> layer stage -> strategy stage.

Rules (DRA v3.0 §1.5, §1.6):

* ``component_stage = max N in {0,1,2}`` such that every criterion at every
  stage ``s`` with ``1 <= s <= N`` for ``(layer, component)`` is satisfied.
* ``layer_stage   = min(component_stage)`` over the three components.
* ``strategy_stage = min(layer_stage)`` over the layers applicable to the
  composition mode.
"""

from __future__ import annotations

from .criteria import CRITERIA
from .types import COMPONENTS, CompositionMode, Component, CriterionStatus, Layer, Stage, StageMatrix


_MODE_LAYERS: dict[CompositionMode, tuple[Layer, ...]] = {
    "A": ("asset", "market", "vault"),
    "B": ("asset", "vault"),
    "C": ("asset", "market"),
    # Mode D (meta-vault) shares the (asset, vault) layer pair with Mode B by
    # design — the *meta-vault's own* layers. The underlying vaults are folded
    # in separately via the ``underlying_vault_stages`` argument to
    # ``strategy_stage``; do not look for them here.
    "D": ("asset", "vault"),
}


def applicable_layers(mode: CompositionMode) -> tuple[Layer, ...]:
    try:
        return _MODE_LAYERS[mode]
    except KeyError as exc:
        raise ValueError(f"unknown mode {mode!r}") from exc


def component_stage(
    layer: Layer,
    component: Component,
    statuses: dict[str, CriterionStatus],
) -> Stage:
    by_stage: dict[int, list[CriterionStatus]] = {1: [], 2: []}
    for c in CRITERIA:
        if c.layer == layer and c.component == component:
            by_stage[c.stage].append(statuses[c.id])

    if not by_stage[1] or not all(s.satisfied for s in by_stage[1]):
        return 0
    if not by_stage[2] or not all(s.satisfied for s in by_stage[2]):
        return 1
    return 2


def layer_stage(layer: Layer, statuses: dict[str, CriterionStatus]) -> Stage:
    return min(component_stage(layer, co, statuses) for co in COMPONENTS)  # type: ignore[return-value]


def build_matrix(statuses: dict[str, CriterionStatus]) -> StageMatrix:
    matrix = StageMatrix()
    for ly in ("asset", "market", "vault"):
        for co in COMPONENTS:
            matrix.cells[ly][co] = component_stage(ly, co, statuses)  # type: ignore[arg-type]
    return matrix


def strategy_stage(
    layer_stages: dict[Layer, Stage],
    mode: CompositionMode,
    *,
    underlying_vault_stages: list[Stage] | None = None,
    meta_vault_stage: Stage | None = None,
) -> Stage:
    """Mode A/B/C: ``min`` across applicable layer stages.

    Mode D (meta-vault): the underlying vaults collectively play the "vault"
    role; the meta-vault contributes its own layer. Strategy stage is the
    minimum across the asset stage, every underlying vault stage, and the
    meta-vault stage.
    """
    if mode == "D":
        if not underlying_vault_stages or meta_vault_stage is None:
            raise ValueError("Mode D requires underlying_vault_stages and meta_vault_stage")
        candidates: list[Stage] = [layer_stages["asset"], meta_vault_stage, *underlying_vault_stages]
        return min(candidates)  # type: ignore[return-value]

    layers = applicable_layers(mode)
    return min(layer_stages[ly] for ly in layers)  # type: ignore[return-value]
