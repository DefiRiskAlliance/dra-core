"""Yearn curation HTML reports -> market and vault attestations.

Yearn curation reports score on a 1..5 scale where **lower = safer**. The
rater inverts the value (``6 - x``) before bucketing so the shared
``threshold_attestations`` helper ("higher = safer") works without a special
case for Yearn.

Two table layouts are supported:

* ``| label | weight% | score |``  (legacy)
* ``| label | score | weight% | ... |``  (current ``yearn/risk-score``
  ``Final Score Calculation`` table; e.g. yvUSDC, yvUSD)
"""

from __future__ import annotations

import re
import urllib.request

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

ROW_RE = re.compile(
    r"\|\s*([^|\n]+?)\s*\|\s*[^|\n]*%\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|",
    re.MULTILINE,
)

ROW_RE_V2 = re.compile(
    r"\|\s*([^|\n]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|\s*[^|\n]*%\s*\|",
    re.MULTILINE,
)

OPS_KEYS = ("centralization", "control", "funds management")
SEC_KEYS = ("audit", "historical", "operational risk", "operational")
ECO_KEYS = ("liquidity",)

# Inverted-score thresholds (we feed ``6 - yearn_score`` to the helper).
S1_THRESHOLD = 3.0
S2_THRESHOLD = 4.0

VAULT_SEC_S1 = ("vault.security.s1.audited", "vault.security.s1.no_critical_findings")
VAULT_SEC_S2 = ("vault.security.s2.multi_audit_bounty", "vault.security.s2.lindy_1y")
VAULT_OPS_S1 = ("vault.operations.s1.timelock_24h", "vault.operations.s1.public_strategy_doc")
VAULT_OPS_S2 = ("vault.operations.s2.immutable_or_long_timelock", "vault.operations.s2.fast_withdrawal")
VAULT_ECO_S1 = (
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
)
VAULT_ECO_S2 = (
    "vault.strategy_economics.s2.proven_track_record",
    "vault.strategy_economics.s2.transparent_positions",
)
MARKET_SEC_S1 = ("market.security.s1.audited", "market.security.s1.lindy_1y")
MARKET_SEC_S2 = ("market.security.s2.multi_audit_bounty", "market.security.s2.lindy_3y")
MARKET_OPS_S1 = ("market.operations.s1.timelock_24h", "market.operations.s1.quality_oracle")
MARKET_OPS_S2 = ("market.operations.s2.timelock_7d_or_immutable", "market.operations.s2.dual_oracle")
MARKET_ECO_S1 = (
    "market.strategy_economics.s1.conservative_params",
    "market.strategy_economics.s1.healthy_utilization",
)
MARKET_ECO_S2 = (
    "market.strategy_economics.s2.proven_under_stress",
    "market.strategy_economics.s2.diversified_collateral",
)


def _fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "agg-scoring-dra/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


class YearnCurationRater(RaterBase):
    @property
    def name(self) -> str:
        return "yearn_curation"

    @property
    def organization(self) -> str | None:
        return "yearn"

    def supported_criteria(self) -> set[str]:
        return {
            *VAULT_SEC_S1, *VAULT_SEC_S2, *VAULT_OPS_S1, *VAULT_OPS_S2, *VAULT_ECO_S1, *VAULT_ECO_S2,
            *MARKET_SEC_S1, *MARKET_SEC_S2, *MARKET_OPS_S1, *MARKET_OPS_S2, *MARKET_ECO_S1, *MARKET_ECO_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        url = ctx.yearn_curation_report_url
        if not url:
            return []
        ck = f"yearn_html:{url}"
        if ck in ctx._cache:
            html = ctx._cache[ck]
        else:
            try:
                html = _fetch_html(url)
            except Exception:
                html = ""
            ctx._cache[ck] = html
        if not html:
            return []

        ops_s: list[float] = []
        sec_s: list[float] = []
        eco_s: list[float] = []
        seen: set[tuple[str, str]] = set()
        for regex in (ROW_RE, ROW_RE_V2):
            for m in regex.finditer(html):
                label_raw, val_s = m.group(1).strip(), m.group(2)
                key = (label_raw.lower(), val_s)
                if key in seen:
                    continue
                seen.add(key)
                label = label_raw.lower()
                try:
                    v = float(val_s)
                except ValueError:
                    continue
                # Yearn 1..5 with lower = safer; invert so higher = safer.
                if not 0.0 < v <= 5.0:
                    continue
                v = 6.0 - v
                if any(k in label for k in OPS_KEYS):
                    ops_s.append(v)
                elif any(k in label for k in SEC_KEYS):
                    sec_s.append(v)
                elif any(k in label for k in ECO_KEYS):
                    eco_s.append(v)

        sec_avg = sum(sec_s) / len(sec_s) if sec_s else None
        ops_avg = sum(ops_s) / len(ops_s) if ops_s else None
        eco_avg = sum(eco_s) / len(eco_s) if eco_s else None

        out: list[CriterionAttestation] = []
        for layer, sec_s1, sec_s2, ops_s1, ops_s2, eco_s1, eco_s2 in (
            ("market", MARKET_SEC_S1, MARKET_SEC_S2, MARKET_OPS_S1, MARKET_OPS_S2, MARKET_ECO_S1, MARKET_ECO_S2),
            ("vault", VAULT_SEC_S1, VAULT_SEC_S2, VAULT_OPS_S1, VAULT_OPS_S2, VAULT_ECO_S1, VAULT_ECO_S2),
        ):
            out.extend(
                threshold_attestations(
                    sec_avg, layer=layer, component="security",  # type: ignore[arg-type]
                    s1_criteria=sec_s1, s2_criteria=sec_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"yearn.report security avg={sec_avg}",
                )
            )
            out.extend(
                threshold_attestations(
                    ops_avg, layer=layer, component="operations",  # type: ignore[arg-type]
                    s1_criteria=ops_s1, s2_criteria=ops_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"yearn.report operations avg={ops_avg}",
                )
            )
            out.extend(
                threshold_attestations(
                    eco_avg, layer=layer, component="strategy_economics",  # type: ignore[arg-type]
                    s1_criteria=eco_s1, s2_criteria=eco_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"yearn.report economics avg={eco_avg}",
                )
            )
        return out
