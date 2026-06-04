# Architecture — MIIP Slice 2

Michael Investment Intelligence Platform (MIIP) is a **manual-input** investment
intelligence system. Slice 2 adds portfolio context, per-monitor sub-indicator scoring,
regime classification, and richer reports — still no live APIs.

Outputs are **heuristic** and based on user-maintained YAML. They are **not** validated
portfolio analytics, live market intelligence, or broker-sourced balances.

Reports include **research posture / possible actions** — the section heading is
**Research posture (not advice)** so acceptance checklists that mention “possible
actions” still map to the same content without imperative trade language.

## Data flow

```
config/portfolio.yaml     ──┐
config/monitors.yaml      ──┤
config/monitor_scoring.yaml ──> loaders ──> AppConfig
config/watchlists.yaml    ──┘
data/market_snapshot.yaml ──> StaticDataSource
       │
       ├─> monitor_scoring.build_all_monitor_statuses()
       ├─> portfolio_analysis.analyse_portfolio()
       ├─> agents + scoring (watchlist instruments)
       ├─> regime.classify_overall_regime()
       └─> insights.build_virtual_committee()
              └─> ReportModel ──> render_daily / render_weekly
```

## CLI

- Primary: `miip`
- Alias: `investment-os` (same Typer app)

## Slice 2 additions

| Module | Role |
| --- | --- |
| `monitor_scoring.py` | Weighted sub-indicator composites per monitor |
| `portfolio_analysis.py` | Holdings, concentration warnings, derived portfolio_risk readings |
| `regime.py` | Overall regime + research posture options |
| `insights.py` | Virtual Investment Committee (deterministic, no LLM) |

## Manual data contract

Update `data/market_snapshot.yaml` after research:

- `monitor_indicators` — per-monitor sub-indicator readings (0–100)
- `metrics` — per-ticker factor inputs for watchlist scoring

Never present manual readings as live market conclusions.

## Future (Slice 3+)

- Optional `DataSource` implementations (files/APIs) with provenance metadata
- Historical store for week-over-week deltas
