# Project Journal

Long-term reviewer memory for MIIP. This journal records high-value context,
review observations, assumptions, and future triggers. It intentionally excludes
routine implementation notes.

## 2026-06-04 - Slice 1 Baseline Review

### Context

Michael Investment Intelligence Platform (MIIP) is intended to become a
long-term investment intelligence platform monitoring:

- Macro Risk
- AI Capex
- China Re-rating
- Robotics / Physical AI
- Portfolio Risk

Cursor Agent is the primary architect and implementer. Shadow CTO role is
independent review, architecture challenge, risk assessment, and project memory.

### Current State

Slice 1 is a deliberately small skeleton:

- Strict YAML configuration for settings, watchlists, agents, and scoring.
- Static placeholder data only.
- Deterministic agents producing 0-100 relative research signals.
- Weighted scoring models.
- Daily and weekly markdown reports with mandatory disclaimers.
- Typer CLI and pytest coverage.

Verification from local venv:

- `29 passed in 0.16s`
- `ruff check .` passed

### Review Observations

The implementation is appropriately scoped for Slice 1. It avoids live data,
databases, scraping, LLMs, or premature infrastructure.

Primary strategic risk: the current skeleton reads as a generic factor-scoring
tool rather than MIIP. The five intended monitor domains are not yet first-class
concepts in config, reports, or models.

This is acceptable for Slice 1 only if the next slice explicitly bends the
system back toward MIIP's investment-monitor architecture.

### Future Review Triggers

- When live or semi-live data sources are introduced, review provenance,
  freshness, retry/failure handling, and source trust boundaries.
- When historical persistence is introduced, review time-series model shape,
  backfill strategy, and report reproducibility.
- When LLM narrative is introduced, require citation/provenance discipline and
  separation between computed signals and generated interpretation.
- When portfolio holdings are introduced, review privacy, account-data handling,
  position sizing semantics, and advice/compliance boundaries.
- When MIIP monitor domains are implemented, confirm the system does not remain
  a generic equity ranker with domain-themed labels.

## 2026-06-04 - Post-MIIP Monitor Refactor Review

### Context

Cursor Agent responded to Shadow CTO feedback by adding first-class MIIP monitor
structure:

- `config/monitors.yaml`
- `src/investment_os/monitors.py`
- monitor readings in `data/market_snapshot.yaml`
- monitor status, thesis framing, risk flags, and data completeness in reports
- tests for monitor fallback and disabled-agent scoring validation

### Review Outcome

The prior strategic risk that Slice 1 was drifting into a generic factor ranker
is substantially reduced. MIIP's five domains are now represented in config,
runtime models, reports, docs, and tests.

Verification from local venv:

- `34 passed in 0.15s`
- `ruff check .` passed
- `investment_os.cli validate-config` succeeded

### Residual Concerns

Monitor "data complete" currently means a scalar monitor signal exists. For
Slice 1 placeholder data this is acceptable, but it could overstate evidence
quality once live data arrives.

The snapshot model rejects missing monitor keys entirely while monitor-building
logic can gracefully handle missing readings. Before live or partial ingestion,
decide whether missing monitor domains should fail validation or produce
explicit incomplete/neutral statuses.

Portfolio data completeness counts all enabled agent neutral fallbacks, even if
a selected scoring model gives an agent zero weight. This is reasonable as a
raw data-quality measure, but report labels should be clear if zero-weight
agents are introduced.

## 2026-06-05 - Slice 2 Independent Review

### Context

Cursor Agent implemented Slice 2 with:

- MIIP as the explicit product name in README/docs/config/reporting.
- `miip` console script plus `investment-os` alias.
- `config/portfolio.yaml` for Michael's approximate manual portfolio.
- Realistic watchlists replacing AAA/BBB placeholders.
- Configurable per-monitor sub-indicator scoring.
- Overall regime classification, research posture, thesis invalidation, portfolio
  concentration warnings, and deterministic Virtual Investment Committee report
  sections.

### Review Outcome

Verdict: PASS WITH FIXES.

The product shape is meaningfully stronger and remains inside the Slice 2
boundary: manual/static data only, no live APIs, no scraping, no LLM calls, no
dashboard, and no broker sync.

Verification:

- `ruff check .` passed.
- `miip` and `investment-os` scripts exist under `.venv/bin` and run.
- `validate-config` passed.
- `pytest` failed: `tests/test_cli_miip.py::test_miip_entry_point_installed`.

### Residual Concerns

The CLI alias test mutates the environment with `pip install -e .` during test
execution and then checks `PATH`, which failed in the current venv. Tests should
not install the package as a side effect.

The `miip version` command still prints `investment-os 0.2.0`, leaving product
naming inconsistent despite the alias being present.

The report's Possible Actions section uses action-like phrases such as "Reduce
risk" and "Add gradually". Although labelled as research-only, these are close
to trade guidance and should remain constrained, generic, and clearly
non-prescriptive.

Portfolio risk derivation is intentionally heuristic. It is useful for Slice 2
but should not be treated as robust risk modelling.

## 2026-06-05 - Slice 2 Re-Review After Fixes

### Context

Cursor Agent addressed the prior Slice 2 review feedback:

- Fixed the brittle CLI alias test so it no longer installs the package during
  pytest.
- Updated `version` output to `miip 0.2.0`.
- Reframed "Possible Actions" as "Research posture (not advice)" with softer,
  non-prescriptive labels.
- Split portfolio policy notes away from concentration warnings.
- Expanded data completeness reporting to separate watchlist metric completeness
  from monitor completeness.

### Review Outcome

Verdict: PASS WITH MINOR CLEANUP.

Verification:

- `47 passed in 0.25s`
- `ruff check .` passed
- `miip version` and `investment-os version` both returned `miip 0.2.0`
- `validate-config` passed
- Daily report generation passed

### Residual Concerns (addressed 2026-06-05 polish)

- README, `docs/ARCHITECTURE.md`, and `docs/SLICE2-ACCEPTANCE.md` align on **research posture** terminology.
- Source docstrings updated from legacy "Investment OS" / "Slice 1" wording where they described Slice 2.
- Review materials state outputs are heuristic and manual-static — not validated analytics or live market intelligence.

## 2026-06-05 - Slice 2 Final Re-Review

### Context

Cursor Agent made another polish pass after the prior Shadow CTO review:

- Added `docs/SLICE2-ACCEPTANCE.md`.
- Aligned README and architecture docs around "research posture (not advice)" while mapping it to acceptance checklists that may say "possible actions".
- Updated stale source docstrings for MIIP/Slice 2 language.
- Preserved manual/static boundaries and report disclaimers.

### Review Outcome

Verdict: PASS WITH MINOR HYGIENE.

Verification:

- `47 passed in 0.27s`
- `ruff check .` passed
- `validate-config` passed
- `miip version` and `investment-os version` returned `miip 0.2.0`
- Daily report generation passed

### Residual Concerns

Only review-pack hygiene remains: `.DS_Store` exists at repo root and is not
ignored. Remove it and add `.DS_Store` to `.gitignore` before packaging or
committing.

Investment logic remains intentionally heuristic and manual-static. This is
acceptable for Slice 2 and now clearly stated in docs/report output.
