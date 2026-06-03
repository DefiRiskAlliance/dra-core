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
    DefiscanRater,
    EulerDefaultsRater,
    FluidDefaultsRater,
    LidoDefaultsRater,
    MellowDefaultsRater,
    PharosRater,
    PhilidorRater,
    RocketPoolDefaultsRater,
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
        "yield_blurb": (
            "USDC deposits routed by the Steakhouse Financial curator across isolated "
            "Morpho Blue markets (typically wstETH/USDC, sDAI/USDC, cbBTC/USDC). Yield is "
            "the interest paid by overcollateralized borrowers in those markets, weighted "
            "by the curator's allocations and net of the vault's performance fee."
        ),
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
        "yield_blurb": (
            "Same Morpho Blue mechanism with Gauntlet's curator allocations across a "
            "conservative blue-chip collateral set. Yield is the blended interest paid by "
            "borrowers in the chosen markets, minus Gauntlet's performance fee."
        ),
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
        "yield_blurb": (
            "PYUSD deposits curated by Steakhouse Financial into PYUSD-denominated Morpho "
            "Blue markets backed by ETH and liquid-staking-token collateral. Yield is the "
            "borrower interest in those isolated PYUSD markets, net of the curator's fee."
        ),
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
        "yield_blurb": (
            "Direct supply into the Aave v3 USDC reserve on Ethereum mainnet. Yield is the "
            "variable supply APY paid by USDC borrowers (with a portion retained as reserve "
            "factor by the protocol). The rate scales with utilisation along Aave's kinked "
            "interest-rate curve and is set by Aave governance."
        ),
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "vaultscan_id": "aave-v3-1-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    },
    {
        "id": "aave-v3-usdt",
        "label": "Aave v3 · USDT (Ethereum)",
        "yield_blurb": (
            "Direct supply into the Aave v3 USDT reserve on Ethereum mainnet. Yield is the "
            "variable supply APY paid by USDT borrowers, set by the Aave-governed interest-rate "
            "curve and current pool utilisation, minus the reserve factor."
        ),
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
        "yield_blurb": (
            "ERC-4626 vault that auto-allocates USDC across Yearn v3 strategies (Aave, "
            "Compound, Curve-Convex stable LPs, etc.) following the targets set in the "
            "Yearn risk-curation report. Net APY is the blended yield from those underlying "
            "strategies minus Yearn's management and performance fees."
        ),
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
        "yield_blurb": (
            "Cross-chain meta-vault that holds multiple underlying USDC yvVaults across "
            "supported chains. Yield is the weighted average of those underlyings' net "
            "APYs, rebalanced according to Yearn's risk-curation scoring and net of the "
            "meta-vault's own fee."
        ),
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
    {
        # wstETH wrapper: 0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0
        "id": "lido-wsteth",
        "label": "Lido · wstETH",
        "yield_blurb": (
            "wstETH is the wrapped, non-rebasing form of Lido's stETH receipt token. "
            "Yield comes from validators staking the underlying ETH on the Beacon Chain "
            "(consensus + execution rewards plus priority-fee tips and MEV). Lido takes "
            "a 10% protocol fee on staking rewards, split between node operators and the DAO."
        ),
        "mode": "B",
        "asset_is_stablecoin": False,
        "philidor_network": "ethereum",
        "vault_address": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
        "vaultscan_id": "lido-wsteth-1-0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",
        "defiscan_market_slug": "lido",
        "defiscan_vault_slug": "lido-wsteth",
    },
    {
        # rETH token: 0xae78736cd615f374d3085123a210448e74fc6393
        "id": "rocketpool-reth",
        "label": "Rocket Pool · rETH",
        "yield_blurb": (
            "rETH is Rocket Pool's non-rebasing liquid staking token, redeemable for a "
            "growing amount of ETH as staking rewards accrue. Yield is the weighted "
            "average return from Rocket Pool's distributed node-operator set (8 ETH "
            "minipools and the original 16 ETH variants), net of the commission paid "
            "to node operators."
        ),
        "mode": "B",
        "asset_is_stablecoin": False,
        "philidor_network": "ethereum",
        "vault_address": "0xae78736Cd615f374D3085123A210448E74Fc6393",
        "vaultscan_id": "rocketpool-reth-1-0xae78736cd615f374d3085123a210448e74fc6393",
        "defiscan_market_slug": "rocketpool",
        "defiscan_vault_slug": "rocketpool-reth",
    },
    {
        # Euler v2 Prime USDC vault — protocol-level entry. Specific vault
        # address omitted (curator picks the EVK vault to onboard); the
        # euler_defaults rater + Defiscan map still fire on the vaultscan_id
        # prefix and the defiscan_*_slug fields.
        "id": "euler-prime-usdc",
        "label": "Euler v2 · Prime USDC",
        "yield_blurb": (
            "USDC supplied into an Euler v2 'Prime' EVK vault — a curator-managed lending "
            "vault built on the post-2024 Euler Vault Kit. Yield is the variable borrow "
            "APY paid by borrowers in the vault, scaled by utilisation and net of the "
            "vault's reserve fee."
        ),
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "vaultscan_id": "euler-prime-usdc-1",
        "defiscan_market_slug": "euler-v2",
        "defiscan_vault_slug": "euler-evk-vault",
    },
    {
        # Fluid USDC vault — protocol-level entry. Specific Fluid vault
        # address omitted; fluid_defaults + Defiscan map (which currently
        # rates Fluid operations at Stage 0) fire on the vaultscan_id prefix.
        "id": "fluid-usdc",
        "label": "Fluid · USDC",
        "yield_blurb": (
            "USDC deposits into Fluid's lending layer (Instadapp's Fluid protocol). "
            "Yield is the variable supply APY paid by overcollateralised borrowers across "
            "Fluid's smart-vault markets, scaled by utilisation and net of the protocol's "
            "reserve factor."
        ),
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "vaultscan_id": "fluid-usdc-1",
        "defiscan_market_slug": "fluid",
        "defiscan_vault_slug": "fluid-vault",
    },
    {
        # Mellow vault framework — protocol-level entry. Curator and specific
        # LRT vault address omitted; mellow_defaults attests framework-level
        # security only (no per-curator claims) and Defiscan supplies the
        # operations stage on the vaultscan_id prefix.
        "id": "mellow-re7-resolv",
        "label": "Mellow · Re7 Resolv Restaked ETH",
        "yield_blurb": (
            "An LRT vault on the Mellow framework operated by the Re7 curator, depositing "
            "ETH into Symbiotic restaking through the Resolv ecosystem. Yield is the "
            "blended return from base ETH staking, Symbiotic restaking rewards, and "
            "curator-selected operator incentives, net of Re7's performance fee."
        ),
        "mode": "B",
        "asset_is_stablecoin": False,
        "vaultscan_id": "mellow-re7-resolv-lrt-1",
        "defiscan_market_slug": "mellow",
        "defiscan_vault_slug": "mellow-vault",
    },
]


_NON_CONTEXT_KEYS = {"label", "id", "yield_blurb"}


def _ctx_from_entry(entry: dict[str, Any]) -> StrategyContext:
    fields = {k: v for k, v in entry.items() if k not in _NON_CONTEXT_KEYS}
    return StrategyContext(**fields)


def _serialise(label: str, entry: dict[str, Any], res: DRAResult) -> dict[str, Any]:
    sources: dict[str, int] = {}
    for att in res.attestations:
        sources[att.source] = sources.get(att.source, 0) + 1

    unsatisfied = []
    applicable = set(applicable_layers(res.mode))  # type: ignore[arg-type]
    blockers = [s for s in res.unsatisfied_criteria() if s.criterion.layer in applicable]
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
        "yield_blurb": entry.get("yield_blurb"),
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
            # Defiscan stage anchor — drives market.operations / vault.operations
            # based on the curated slug map in providers/defiscan.py. Triggered
            # by ctx.defiscan_market_slug / ctx.defiscan_vault_slug.
            DefiscanRater(),
            # Protocol defaults — match on ctx.vaultscan_id prefix
            # (lido-*, rocketpool-* | rp-*, euler-*, fluid-*, mellow-*).
            LidoDefaultsRater(),
            RocketPoolDefaultsRater(),
            EulerDefaultsRater(),
            FluidDefaultsRater(),
            MellowDefaultsRater(),
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
        "raters": [
            "pharos", "yearn_curation", "philidor", "vaultscan",
            "aave_defaults", "defiscan",
            "lido_defaults", "rocketpool_defaults", "euler_defaults",
            "fluid_defaults", "mellow_defaults",
        ],
        "entries": serialised,
    }

    out_path = ROOT / "docs" / "ratings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    print(f"\nWrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
