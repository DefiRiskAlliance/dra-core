"""Generate the static rating snapshot consumed by ``docs/ratings.html``.

This is the production driver for the DRA Pages site (the static GitHub
Pages site under ``docs/``). It scores a curated set of vaults using the
four raters the Charter and Methodology pages call out — Pharos, Yearn
Risk Curation, Philidor, Vaultscan — and writes a compact JSON snapshot
to ``docs/ratings.json``.

The snapshot schema is intentionally narrow (we only emit what the page
actually renders, no internal-only ``methodology_version`` etc.) so that
the JSON file stays small and human-diffable in PR review:

    {
      "generated_at": "2026-04-28T09:00:00Z",
      "raters": ["pharos", "yearn_curation", "philidor", "vaultscan"],
      "entries": [
        {
          "id": "...",
          "label": "...",
          "mode": "A" | "B" | "C" | "D",
          "applicable_layers": ["asset", "market", "vault"],
          "strategy_stage": 0 | 1 | 2,
          "layer_stages": {"asset": 0, "market": 0, "vault": 0},
          "matrix": {layer: {component: stage}},
          "sources": {rater_name: attestation_count},
          "unsatisfied": [
            {
              "criterion_id": "...",
              "layer": "...",
              "component": "...",
              "stage": 1 | 2,
              "description": "...",
              "violations": [{"source": "...", "evidence": "..."}],
              "verifications": [{"source": "...", "evidence": "..."}]
            }
          ]
        }
      ]
    }

Run from the repo root::

    python3 examples/dra_site_snapshot.py

Adapters that lack their respective env keys (``VAULTSCAN_SUPABASE_*``,
``PHAROS_API_KEY``) skip silently — the script still runs and you'll see
Stage 0 for cells with no data.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_dotenv(path: Path) -> None:
    """Lightweight ``KEY=VALUE`` loader; existing env vars win."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


_load_dotenv(ROOT / ".env")

from methodology import COMPONENTS, DRAEngine, DRAResult, LAYERS, StrategyContext
from methodology.compose import applicable_layers
from providers import (
    AaveDefaultsRater,
    PharosRater,
    PhilidorRater,
    VaultscanRater,
    YearnCurationRater,
)

# Curated entries chosen so each of the four raters attests on at least two
# entries. Addresses are mainnet (chain id 1) unless noted. Vaultscan id format:
# ``morpho-{chainId}-{vaultAddress lower}`` for Morpho vaults,
# ``aave-v3-{chainId}-{underlyingTokenAddress lower}`` for Aave reserves,
# ``yearn-v3-{chainId}-{vaultAddress lower}`` for Yearn v3 vaults.
ENTRIES: list[dict[str, Any]] = [
    {
        "id": "morpho-steakhouse-usdc",
        "label": "Morpho · Steakhouse USDC",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0xBEEF01735c132Ada46AA9aA4c54623caA92A64CB",
        "philidor_fill_market_from_vault": True,
        "vaultscan_id": "morpho-1-0xbeef01735c132ada46aa9aa4c54623caa92a64cb",
    },
    {
        "id": "morpho-gauntlet-usdc-core",
        "label": "Morpho · Gauntlet USDC Core",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0x8eB67A509616cd6A7c1B3c8C21D48FF57df3d458",
        "philidor_fill_market_from_vault": True,
        "vaultscan_id": "morpho-1-0x8eb67a509616cd6a7c1b3c8c21d48ff57df3d458",
    },
    {
        "id": "morpho-steakhouse-pyusd",
        "label": "Morpho · Steakhouse PYUSD",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "pyusd-paypal",
        "philidor_network": "ethereum",
        "vault_address": "0xbEEf02e5E13584ab96848af90261f0C8Ee04722a",
        "philidor_fill_market_from_vault": True,
        "vaultscan_id": "morpho-1-0xbeef02e5e13584ab96848af90261f0c8ee04722a",
    },
    {
        "id": "aave-v3-usdc",
        "label": "Aave v3 · USDC (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "vaultscan_id": "aave-v3-1-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    },
    {
        "id": "aave-v3-usdt",
        "label": "Aave v3 · USDT (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdt-tether",
        "vaultscan_id": "aave-v3-1-0xdac17f958d2ee523a2206206994597c13d831ec7",
    },
    {
        # Yearn v3 yvUSDC. Risk-score raw markdown lives at
        # github.com/yearn/risk-score/blob/master/reports/report/yearn-yvusdc.md
        "id": "yearn-v3-yvusdc",
        "label": "Yearn v3 · yvUSDC",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0xBe53A109B494E5c9f97b9Cd39Fe969BE68BF6204",
        "philidor_fill_market_from_vault": True,
        "vaultscan_id": "yearn-v3-1-0xbe53a109b494e5c9f97b9cd39fe969be68bf6204",
        "yearn_curation_report_url": (
            "https://raw.githubusercontent.com/yearn/risk-score/master/reports/report/yearn-yvusdc.md"
        ),
    },
    {
        # Yearn v3 yvUSD (cross-chain USDC vault). yearn-yvusd.md report.
        "id": "yearn-v3-yvusd",
        "label": "Yearn v3 · yvUSD",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0x696d02Db93291651ED510704c9b286841d506987",
        "philidor_fill_market_from_vault": True,
        "vaultscan_id": "yearn-v3-1-0x696d02db93291651ed510704c9b286841d506987",
        "yearn_curation_report_url": (
            "https://raw.githubusercontent.com/yearn/risk-score/master/reports/report/yearn-yvusd.md"
        ),
    },
]


def _ctx_from_entry(entry: dict[str, Any]) -> StrategyContext:
    fields = {k: v for k, v in entry.items() if k not in {"label", "id"}}
    return StrategyContext(**fields)


def _serialise(label: str, entry: dict[str, Any], res: DRAResult) -> dict[str, Any]:
    sources: dict[str, int] = {}
    for att in res.attestations:
        sources[att.source] = sources.get(att.source, 0) + 1

    unsatisfied = []
    blockers = res.unsatisfied_criteria()
    blockers.sort(key=lambda s: (s.criterion.stage, s.criterion.id))
    for status in blockers:
        unsatisfied.append(
            {
                "criterion_id": status.criterion.id,
                "layer": status.criterion.layer,
                "component": status.criterion.component,
                "stage": status.criterion.stage,
                "description": status.criterion.description,
                "violations": [
                    {"source": a.source, "evidence": a.evidence}
                    for a in status.violations
                ],
                "verifications": [
                    {"source": a.source, "evidence": a.evidence}
                    for a in status.verifications
                ],
            }
        )

    matrix: dict[str, dict[str, int]] = {}
    for ly in LAYERS:
        matrix[ly] = {co: int(res.matrix.cells[ly][co]) for co in COMPONENTS}

    return {
        "id": entry["id"],
        "label": label,
        "mode": res.mode,
        "applicable_layers": list(applicable_layers(res.mode)),  # type: ignore[arg-type]
        "strategy_stage": int(res.strategy_stage),
        "layer_stages": {ly: int(s) for ly, s in res.layer_stages.items()},
        "matrix": matrix,
        "sources": dict(sorted(sources.items())),
        "unsatisfied": unsatisfied,
    }


def main() -> None:
    engine = DRAEngine(
        [
            VaultscanRater(),
            PharosRater(),
            PhilidorRater(),
            YearnCurationRater(),
            AaveDefaultsRater(),
        ]
    )

    serialised: list[dict[str, Any]] = []
    for entry in ENTRIES:
        ctx = _ctx_from_entry(entry)
        res = engine.score(ctx)
        serialised.append(_serialise(entry["label"], entry, res))
        print(
            f"  {entry['label']:<36} mode={res.mode} "
            f"strategy={res.strategy_stage} "
            f"layers={dict(res.layer_stages)} "
            f"sources={list(serialised[-1]['sources'].keys())}"
        )

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "methodology_version": "v3.0",
        "raters": ["pharos", "yearn_curation", "philidor", "vaultscan", "aave_defaults"],
        "entries": serialised,
    }

    out_path = ROOT / "docs" / "ratings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    print(f"\nWrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
