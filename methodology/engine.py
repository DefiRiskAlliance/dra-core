"""DRA v3.0 engine: collect attestations -> resolve -> roll up to stages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .compose import applicable_layers, build_matrix, layer_stage, strategy_stage
from .criteria import get_criterion
from .entities import ManualOverride, StrategyContext
from .merge import resolve_attestations
from .types import (
    COMPONENTS,
    CriterionAttestation,
    CriterionStatus,
    Layer,
    Stage,
    StageMatrix,
)

# Operator-identity strings that are clearly not accountable identities. Used to
# reject manual_attestations that try to re-introduce the legacy "source=manual"
# backdoor.
_BLOCKED_MANUAL_SOURCES = {"", "manual", "manual override", "operator"}


class Rater(Protocol):
    name: str
    organization: str | None

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]: ...

    def supported_criteria(self) -> set[str]: ...


@dataclass
class DRAResult:
    strategy_stage: Stage
    layer_stages: dict[Layer, Stage]
    matrix: StageMatrix
    criteria_status: dict[str, CriterionStatus]
    attestations: list[CriterionAttestation] = field(default_factory=list)
    methodology_version: str = "v3.0"
    mode: str = "A"
    underlying_vault_stages: list[Stage] | None = None
    meta_vault_stage: Stage | None = None
    skipped_raters: list[str] = field(default_factory=list)
    """Raters dropped because their ``organization`` matches the rated entity's
    ``protocol_organization`` (self-rating filter)."""

    def applicable_layers(self) -> tuple[Layer, ...]:
        return applicable_layers(self.mode)  # type: ignore[arg-type]

    def unsatisfied_criteria(self) -> list[CriterionStatus]:
        return [s for s in self.criteria_status.values() if not s.satisfied]


def _validate_manual_attestation(a: CriterionAttestation) -> None:
    src = (a.source or "").strip().lower()
    if src in _BLOCKED_MANUAL_SOURCES:
        raise ValueError(
            f"manual attestation on {a.criterion_id!r} must declare an "
            "accountable operator in `source` (not empty, not 'manual')"
        )
    if not (a.evidence or "").strip():
        raise ValueError(
            f"manual attestation on {a.criterion_id!r} must include a "
            "non-empty `evidence` string (rationale + PR/issue link)"
        )


def _override_to_attestation(o: ManualOverride) -> CriterionAttestation:
    crit = get_criterion(o.criterion_id)
    if crit.layer != o.layer or crit.component != o.component:
        raise ValueError(
            f"manual override {o.criterion_id!r} is registered as "
            f"{crit.layer}/{crit.component}, not {o.layer}/{o.component}"
        )
    return CriterionAttestation(
        layer=o.layer,
        component=o.component,
        criterion_id=o.criterion_id,
        verdict=o.verdict,
        source=o.operator,
        evidence=f"{o.rationale} ({o.rationale_ref})",
    )


def _audit_record(o: ManualOverride, ctx: StrategyContext) -> dict[str, object]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "operator": o.operator,
        "rationale": o.rationale,
        "rationale_ref": o.rationale_ref,
        "layer": o.layer,
        "component": o.component,
        "criterion_id": o.criterion_id,
        "verdict": o.verdict,
        "methodology_version": ctx.methodology_version,
        "mode": ctx.mode,
        "protocol_organization": ctx.protocol_organization,
    }


class DRAEngine:
    """Drives a list of raters, resolves attestations, returns a ``DRAResult``."""

    def __init__(
        self,
        raters: list[Rater],
        *,
        manual_override_log_path: Path | str | None = None,
    ) -> None:
        self.raters = list(raters)
        self.manual_override_log_path = (
            Path(manual_override_log_path) if manual_override_log_path else None
        )

    def _append_audit(self, record: dict[str, object]) -> None:
        if self.manual_override_log_path is None:
            return
        self.manual_override_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.manual_override_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    def score(
        self,
        ctx: StrategyContext,
        *,
        underlying_vault_stages: list[Stage] | None = None,
        meta_vault_stage: Stage | None = None,
    ) -> DRAResult:
        all_attestations: list[CriterionAttestation] = []
        skipped: list[str] = []

        for r in self.raters:
            rater_org = getattr(r, "organization", None)
            if rater_org and ctx.protocol_organization and rater_org == ctx.protocol_organization:
                skipped.append(r.name)
                continue
            attestations = r.attest(ctx)
            for a in attestations:
                all_attestations.append(
                    CriterionAttestation(
                        layer=a.layer,
                        component=a.component,
                        criterion_id=a.criterion_id,
                        verdict=a.verdict,
                        source=a.source or r.name,
                        evidence=a.evidence,
                        weight=a.weight,
                        timestamp=a.timestamp,
                        as_of_block=a.as_of_block,
                    )
                )

        for o in ctx.manual_overrides:
            all_attestations.append(_override_to_attestation(o))
            self._append_audit(_audit_record(o, ctx))

        for a in ctx.manual_attestations:
            _validate_manual_attestation(a)
            all_attestations.append(a)

        statuses = resolve_attestations(all_attestations)
        matrix = build_matrix(statuses)
        layers: dict[Layer, Stage] = {
            ly: layer_stage(ly, statuses) for ly in ("asset", "market", "vault")
        }
        strat = strategy_stage(
            layers,
            ctx.mode,
            underlying_vault_stages=underlying_vault_stages,
            meta_vault_stage=meta_vault_stage,
        )

        return DRAResult(
            strategy_stage=strat,
            layer_stages=layers,
            matrix=matrix,
            criteria_status=statuses,
            attestations=all_attestations,
            methodology_version=ctx.methodology_version,
            mode=ctx.mode,
            underlying_vault_stages=underlying_vault_stages,
            meta_vault_stage=meta_vault_stage,
            skipped_raters=skipped,
        )


__all__ = ["COMPONENTS", "DRAEngine", "DRAResult", "ManualOverride", "Rater"]
