"""Resolve provider attestations into a per-criterion satisfied/unsatisfied status.

Resolution rule (DRA v3.0 §6):

- If at least one provider files ``verified`` AND no provider files ``violated``
  for criterion ``c`` -> ``c`` is **satisfied**.
- If any provider files ``violated`` -> ``c`` is **unsatisfied**, regardless of
  how many ``verified`` attestations exist (default-to-worse).
- If no attestations exist or all are ``unknown`` -> ``c`` is **unsatisfied**
  (opacity is penalised).
- Attestations older than ``criterion.max_age_days`` are dropped from the
  rule (treated as ``unknown``) and returned on ``CriterionStatus.stale``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from .criteria import CRITERIA, get_criterion
from .types import Criterion, CriterionAttestation, CriterionStatus


def _is_stale(att: CriterionAttestation, crit: Criterion, now: datetime) -> bool:
    ts = att.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return now - ts > timedelta(days=crit.max_age_days)


def _resolve_one(
    criterion: Criterion,
    atts: list[CriterionAttestation],
    now: datetime,
) -> CriterionStatus:
    fresh: list[CriterionAttestation] = []
    stale: list[CriterionAttestation] = []
    for a in atts:
        (stale if _is_stale(a, criterion, now) else fresh).append(a)
    verifications = [a for a in fresh if a.verdict == "verified"]
    violations = [a for a in fresh if a.verdict == "violated"]
    return CriterionStatus(
        criterion=criterion,
        satisfied=bool(verifications) and not violations,
        verifications=verifications,
        violations=violations,
        stale=stale,
    )


def resolve_attestations(
    attestations: Iterable[CriterionAttestation],
    *,
    now: datetime | None = None,
) -> dict[str, CriterionStatus]:
    """Group attestations by criterion id and apply the resolution rule.

    Unknown criterion ids are silently dropped (with a debug-friendly accumulator)
    so a stale provider mapping cannot corrupt the matrix. Tests should validate
    that adapters only attest known criteria.

    ``now`` is exposed so callers (and tests) can freeze the staleness clock.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    grouped: dict[str, list[CriterionAttestation]] = defaultdict(list)
    for a in attestations:
        grouped[a.criterion_id].append(a)

    statuses: dict[str, CriterionStatus] = {}
    for criterion in CRITERIA:
        statuses[criterion.id] = _resolve_one(criterion, grouped.get(criterion.id, []), now)

    for cid, atts in grouped.items():
        if cid in statuses:
            continue
        try:
            criterion = get_criterion(cid)
        except KeyError:
            continue
        statuses[cid] = _resolve_one(criterion, atts, now)

    return statuses
