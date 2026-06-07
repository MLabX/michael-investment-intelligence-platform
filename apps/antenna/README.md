# Antenna MVP

**Mission: Opportunity Discovery**

Antenna automatically surfaces **signals worth paying attention to** across five themes:
**AI · Robotics · Space · China · Macro**.

This is **not** stock picking, investment advice, or portfolio management.
**Discovery first. Research second. Action later.**

The daily output is one Markdown brief. A human decides what matters.

---

## What this validates (30-day run)

| Mode | What it proves |
|---|---|
| **Heuristic** (no API key) | Pipeline reliability — fetch, dedup, render, CI, daily cron. **Does NOT validate discovery quality.** |
| **LLM** (`OPENAI_API_KEY` set) | Whether the brief is actually *useful*. **This is the only mode that validates product value.** |

Do not mistake a green heuristic run for a good brief. Heuristic mode validates plumbing only.

---

## Architecture

Single linear pipeline. No frameworks, no database, no server, no frontend.

```
feeds.yaml → fetch.py → seen.py → analyze.py → brief.py → reports/discovery/daily/YYYY-MM-DD.md
              (RSS +      (cross-day   (LLM or
               timeout)    dedup)      heuristic)
```

| Module | Responsibility |
|---|---|
| `config.py` | Load `feeds.yaml` (sources + settings). |
| `fetch.py` | Pull RSS with **per-feed timeout**; skip broken/slow feeds; never fail the run. |
| `seen.py` | Cross-day dedup via `data/antenna/seen.json` — repeats skipped unless materially updated. |
| `analyze.py` | Select signals + write summary / why-it-matters / confidence. |
| `brief.py` | Render Markdown (incl. "Nothing Important Today"). |
| `main.py` | CLI entry: `python -m antenna` (with `PYTHONPATH=apps`). |

---

## Run locally

From repo root:

```bash
pip install -r apps/antenna/requirements.txt

# Heuristic — validates plumbing only:
PYTHONPATH=apps python -m antenna --verbose

# LLM — validates discovery quality (required for 30-day evaluation):
export OPENAI_API_KEY=sk-...
export ANTENNA_MODEL=gpt-4o-mini   # optional
PYTHONPATH=apps python -m antenna --verbose
```

Writes `reports/discovery/daily/YYYY-MM-DD.md` (Sydney calendar date).

Useful flags: `--hours N`, `--out DIR`, `--seen PATH`, `--no-dedup` (debug), `--feeds PATH`.

---

## Data sources

19 public RSS feeds in `feeds.yaml`. Dead or slow feeds are skipped automatically.

| Theme | Sources |
|---|---|
| **AI** | MIT Technology Review · Ars Technica AI · The Decoder · Hugging Face Blog · arXiv cs.AI |
| **Robotics** | IEEE Spectrum Robotics · The Robot Report · arXiv cs.RO |
| **Space** | SpaceNews · Ars Technica Space · Spaceflight Now |
| **China** | SCMP China · SCMP Economy · Sixth Tone |
| **Macro** | Federal Reserve Press · NY Fed Liberty Street · ECB Press · Calculated Risk · Marginal Revolution |

---

## Daily automation

`.github/workflows/antenna-daily.yml` runs at **20:00 UTC** (~Sydney morning).

**DST note:** GitHub cron does not adjust for daylight saving. At 20:00 UTC the brief
arrives at approximately:
- **~06:00** during AEST (Apr–Oct)
- **~07:00** during AEDT (Oct–Apr)

Set repo secret **`OPENAI_API_KEY`** for LLM mode (strongly recommended for validation).
Optional repo variable **`ANTENNA_MODEL`**.

The workflow commits:
- `reports/discovery/daily/YYYY-MM-DD.md`
- `data/antenna/seen.json` (cross-day dedup state)

Both are gitignored locally; CI force-adds them.

---

## CI

`.github/workflows/antenna-ci.yml` runs on Antenna changes:
- `ruff check .`
- `ruff format --check .`
- `pytest tests/test_antenna.py`

---

## Output format

```markdown
# Morning Discovery Brief
## Top Signals Today
### N. <title>
- Source
- Summary
- Why it matters
- Related themes
- Confidence
```

Or **"Nothing Important Today."** — a quiet day is a valid result.

---

## Explicit non-goals

No investment advice · no stock picks · no LangGraph/CrewAI · no vector DB · no cloud
architecture · no dashboards · no accounts · no microservices · no theme/contradiction/capital-flow
engines. If it isn't needed to produce a reliable daily brief, it doesn't belong here.
