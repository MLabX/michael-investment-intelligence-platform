# Agent Architecture (MIIP)

MIIP is organised around **five investment-monitor domains** defined in
`config/monitors.yaml`. Slice 2 scores each monitor from manual sub-indicator
readings in `data/market_snapshot.yaml` (`monitor_indicators:`).

## MIIP monitors (platform-wide)

| ID | Monitor |
| --- | --- |
| `macro_risk` | Macro Risk |
| `ai_capex` | AI Capex |
| `china_rerating` | China Re-rating |
| `robotics_physical_ai` | Robotics / Physical AI |
| `portfolio_risk` | Portfolio Risk |

Monitor signals are 0-100 **relative research signals**, not predictions. Missing
readings use neutral 50 with explicit provenance (see reports).

## Factor agents (Portfolio Risk — per instrument)

Under Portfolio Risk, four deterministic factor agents score watchlist instruments
from `metrics:` in the snapshot:

| Agent | type | Input | Mapping |
| --- | --- | --- | --- |
| Momentum | `momentum` | `momentum` | direct |
| Value | `value` | `value` | direct |
| Quality | `quality` | `quality` | direct |
| Risk | `risk` | `volatility` | inverted (100 - volatility) |

Missing instrument metrics return neutral 50 with `used_neutral_fallback=True`.

## Adding capability

- **New monitor domain:** extend `MIIP_MONITOR_IDS`, `config/monitors.yaml`, snapshot
  `monitors:`, and `monitors.py` / reporting.
- **New factor agent:** add agent class, register in `AGENT_TYPES`, update
  `config/agents.yaml` and scoring weights.

## Safety

Agents and monitors produce research signals only — not financial advice.
