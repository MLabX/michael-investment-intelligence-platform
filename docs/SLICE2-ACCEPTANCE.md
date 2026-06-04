# Slice 2 Acceptance Checklist

Use this when signing off MIIP Slice 2 for review-pack delivery.

## Product framing

- Product name: **MIIP** (Michael Investment Intelligence Platform)
- Primary CLI: **`miip`** (`investment-os` remains a backward-compatible alias)
- Data mode: **manual/static only** — not live market data, broker sync, or validated analytics

## Functional criteria

| # | Criterion | How to verify |
| --- | --- | --- |
| 1 | `miip validate-config` | Exits 0 on repo `config/` + `data/` |
| 2 | `miip score` | Ranked watchlist output |
| 3 | `miip report daily` | Writes markdown under `reports/daily/` |
| 4 | `miip report weekly` | Writes markdown under `reports/weekly/` |
| 5 | `miip version` | Prints `miip 0.2.0` |
| 6 | Portfolio config | `config/portfolio.yaml` — Michael holdings |
| 7 | Monitor scoring | `config/monitor_scoring.yaml` + `monitor_indicators` in snapshot |
| 8 | pytest | `pytest` — all pass |
| 9 | ruff | `ruff check .` — pass |

## Report sections (Slice 2)

Reports must include (wording may vary slightly):

- Investment thesis framing
- Overall regime (Risk On / Balanced / Cautious / Defensive)
- **Research posture / possible actions** — rendered as the heading
  `## Research posture (not advice)` (non-prescriptive deliberation options, not trade
  instructions). Checklist items that say “Possible Actions” mean this section.
- Virtual Investment Committee
- Michael's portfolio (manual entry)
- Portfolio concentration warning
- Portfolio policy notes (separate from concentration)
- Thesis invalidation conditions
- MIIP monitor status + sub-indicators
- Data completeness (watchlist vs monitor)
- Manual/static data notice + disclaimer

## Safety language

- No imperative trade instructions (“buy”, “sell”, “add gradually”, “reduce risk” as commands)
- Research posture items are descriptive (e.g. “No action implied — research only”)
- Reports state data is manual/static, not live market conclusions

## Explicit non-goals (Slice 2)

- Live APIs, scraping, LLMs, databases, dashboards, automated trading
