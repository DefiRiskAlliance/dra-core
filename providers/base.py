"""Base class for DRA v3.0 provider adapters.

A rater observes a ``StrategyContext`` and returns a list of
``CriterionAttestation`` records. Each attestation carries a verdict —
``verified``, ``violated``, or ``unknown`` — for one specific criterion id from
``methodology.criteria.CRITERIA``.

Adapters MUST also expose ``supported_criteria()`` so that operators can audit
which subset of the rubric a given provider claims to cover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation


class RaterBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def organization(self) -> str | None:
        """Slug of the organisation behind this rater. When it matches the
        rated protocol's ``protocol_organization`` the engine drops the
        rater's attestations to avoid self-rating."""
        return None

    @abstractmethod
    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]: ...

    @abstractmethod
    def supported_criteria(self) -> set[str]: ...

    def _validate(self, attestations: list[CriterionAttestation]) -> list[CriterionAttestation]:
        """Helper for adapters: drop attestations referencing unknown criteria."""
        valid_ids = all_criterion_ids()
        return [a for a in attestations if a.criterion_id in valid_ids]
