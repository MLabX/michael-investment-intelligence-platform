# MIIP — Michael Investment Intelligence Platform

**Product name:** MIIP  
**CLI:** `miip` (primary) · `investment-os` (backward-compatible alias)  
**Slice 2:** manual-input investment intelligence for Michael — no live APIs.

> **Research and decision support only.** MIIP uses manually entered readings and
> portfolio values. Outputs are **not** financial advice, live market data, or trade
> signals. Update `config/portfolio.yaml` and `data/market_snapshot.yaml` after your
> own research.

## What MIIP does (Slice 2)

- **Five MIIP monitors** with configurable sub-indicators, weights, and thresholds:
  Macro Risk, AI Capex, China Re-rating, Robotics / Physical AI, Portfolio Risk.
- **Michael's portfolio** (`config/portfolio.yaml`) — holdings, cash, risk constraints.
- **Research watchlists** — `current_holdings`, thematic lists, ETF candidates.
- **Overall regime** — Risk On / Balanced / Cautious / Defensive.
- **Reports** — Virtual Investment Committee, **research posture / possible actions**
  (rendered as “Research posture (not advice)” — not trade instructions), thesis
  invalidation, concentration warnings, disclaimers.

**Important:** Outputs are **heuristic** and based on **manual/static** inputs only.
They are not validated portfolio analytics, live market intelligence, or broker data.

**Not included:** live data, APIs, scraping, LLMs, broker sync, automated trading.

## Requirements

- Python 3.12+
- Typer, Pydantic v2, PyYAML (dev: pytest, ruff)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
miip version
miip validate-config
miip watchlists
miip score
miip score --watchlist ai_infrastructure --model defensive
miip report daily --date 2026-06-05
miip report weekly --date 2026-06-05
```

`investment-os` accepts the same commands.

## Configuration

| File | Purpose |
| --- | --- |
| `config/portfolio.yaml` | Michael's holdings, cash, risk constraints |
| `config/monitors.yaml` | Monitor theses and invalidation conditions |
| `config/monitor_scoring.yaml` | Per-monitor sub-indicators and weights |
| `config/watchlists.yaml` | Research watchlists |
| `config/agents.yaml` | Portfolio factor agents |
| `config/scoring.yaml` | Instrument scoring models |
| `config/settings.yaml` | Defaults and regime thresholds |
| `data/market_snapshot.yaml` | Manual monitor + instrument readings |

## Update your data

1. Edit **`config/portfolio.yaml`** when position sizes change.
2. Edit **`data/market_snapshot.yaml`** after research (monitor indicators + metrics).
3. Run `miip validate-config` then `miip report daily`.

## Testing

```bash
pytest
ruff check .
ruff format .
```

## Layout

Package: `src/investment_os/` — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/SLICE2-ACCEPTANCE.md](docs/SLICE2-ACCEPTANCE.md).

## Roadmap

- Slice 3+: optional file/API ingestion behind `DataSource` (still no advice engine).
- History persistence for week-over-week reports.
