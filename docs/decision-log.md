# Decision Log

High-value product and architecture decisions for MIIP. This log captures
reasoning, assumptions, rejected alternatives, risks, and review triggers.

## 2026-06-04 - Slice 1 Is a Skeleton, Not an Intelligence Engine

### Decision

Slice 1 will establish the operating structure only: configuration, repository
layout, CLI, report generation, placeholder scoring, and tests.

### Reasoning

The project needs a stable control plane before adding volatile data sources,
analytics, LLMs, or portfolio workflows. A deterministic skeleton makes future
changes reviewable and keeps early complexity low.

### Rejected Alternatives

- Start with live market data ingestion.
- Start with LLM-generated investment narratives.
- Start with dashboard/UI work.
- Start with database-backed history.

### Risks

The skeleton may drift into a generic scoring demo unless MIIP's five monitor
domains become first-class soon.

### Review Trigger

Before Slice 2 is considered complete, confirm that at least one MIIP monitor
domain has a concrete data contract, report section, and risk/status model.

## 2026-06-04 - Use Static Placeholder Data in Slice 1

### Decision

All Slice 1 outputs use static, hand-authored placeholder data. Reports and docs
must label it as non-market data.

### Reasoning

This preserves deterministic tests and avoids premature coupling to source
quality, API limits, vendor terms, authentication, retries, and stale data.

### Rejected Alternatives

- Pull free market data immediately.
- Scrape web sources.
- Manually paste real figures into static files.

### Risks

Placeholder values can create false confidence if the report format looks too
real. Missing metrics currently become neutral scores, which can hide data
quality issues later.

### Review Trigger

When real data arrives, add explicit provenance and data completeness reporting.

## 2026-06-04 - Deterministic Agents Emit Relative 0-100 Signals

### Decision

Agents produce deterministic 0-100 relative research signals. Higher is better.
Scores are not forecasts, recommendations, or expected returns.

### Reasoning

A uniform signal contract simplifies scoring, ranking, reporting, and tests.
Determinism makes early behavior explainable and reproducible.

### Rejected Alternatives

- Have agents emit free-form narratives first.
- Have agents emit price targets or expected returns.
- Use incomparable domain-specific score scales in Slice 1.

### Risks

The 0-100 abstraction may flatten materially different risk types. Later domain
monitors may need richer state than a single scalar.

### Review Trigger

When monitor-specific agents appear, review whether each domain needs status,
confidence, trend, horizon, and evidence fields in addition to score.

## 2026-06-04 - Reports Must Stay Research-Only

### Decision

Every generated report must include research-only and placeholder-data
disclaimers where applicable.

### Reasoning

MIIP is decision support, not financial advice. Safety language must be enforced
as part of the product surface, not left to habit.

### Rejected Alternatives

- Put the disclaimer only in the README.
- Rely on user understanding that Slice 1 is a demo.

### Risks

As reports become more polished, users may treat them as recommendations unless
language discipline remains strict.

### Review Trigger

Whenever report generation changes, check for advice-like wording such as
"buy", "sell", "should", "will rise", "will fall", or guaranteed outcomes.

## 2026-06-04 - Make MIIP Monitor Domains First-Class in Slice 1

### Decision

MIIP's five monitor domains are represented directly in configuration, snapshot
data, runtime report models, and markdown reports.

### Reasoning

This prevents the platform from becoming a generic instrument-ranking tool. The
factor-agent scoring system remains useful, but it is now explicitly framed as
one input to Portfolio Risk rather than the whole product.

### Rejected Alternatives

- Keep monitors only in documentation.
- Rename generic factor sections with MIIP labels without adding monitor data
  contracts.
- Build domain-specific live data ingestion before establishing monitor shape.

### Risks

Monitor signals are still placeholder scalars. They can communicate false
precision if not paired with provenance, evidence fields, freshness, and
confidence once real data is introduced.

### Review Trigger

Before Slice 2 completion, at least one monitor should have concrete input
fields beyond a scalar signal: evidence/provenance, freshness, confidence,
change drivers, and risk flags.

## 2026-06-04 - Surface Neutral Fallbacks and Data Completeness

### Decision

Missing monitor or instrument metrics use neutral fallback where possible, and
reports surface fallback counts, missing metric events, and warnings.

### Reasoning

Neutral defaults keep Slice 1 robust while reducing the risk that unknown data
is mistaken for average observed data.

### Rejected Alternatives

- Fail every report on any missing metric.
- Silently use neutral scores without report-level warnings.
- Penalize missing values before defining source quality and completeness rules.

### Risks

The snapshot currently requires all five monitor keys, so missing monitor
domains fail validation before the graceful fallback path can run. Also, "data
complete" currently means signal-present, not evidence-complete.

### Review Trigger

Before real ingestion, define a missing-data policy per monitor and decide
whether partial monitor snapshots should be valid with explicit incomplete
statuses.

## 2026-06-05 - Keep Slice 2 Manual-Static While Adding Portfolio Context

### Decision

Slice 2 adds Michael-specific portfolio configuration, realistic watchlists,
monitor sub-indicator scoring, regime classification, and richer reports while
remaining fully manual/static.

### Reasoning

This gives MIIP a more useful review workflow without crossing into live data,
broker integration, automation, LLM synthesis, or dashboard scope.

### Rejected Alternatives

- Add live market APIs for watchlist metrics.
- Scrape current macro or company data.
- Generate report prose with LLM calls.
- Build a dashboard before the report workflow is stable.

### Risks

Manual portfolio and monitor readings can feel more concrete than their data
quality warrants. "Possible actions" language can drift toward advice if not
tightly framed.

### Review Trigger

Before publishing a review pack, fix the failing CLI alias test and make the
`version` command identify the product as MIIP.

## 2026-06-05 - Rename Possible Actions to Research Posture

### Decision

The report section formerly framed as "Possible Actions" is now rendered as
"Research posture (not advice)" with non-prescriptive options.

### Reasoning

MIIP is personal, portfolio-aware decision support. Action-like language can
read as trade guidance even with disclaimers. The new wording keeps the
deliberation value while reducing financial-advice risk.

### Rejected Alternatives

- Keep "Possible Actions" as the report heading.
- Remove the section entirely.
- Use direct trade-like labels such as "Add gradually" or "Reduce risk".

### Risks

External acceptance checklists may still look for the literal "Possible
Actions" phrase. The docs and review pack should align on the safer terminology.

### Review Trigger

Before packaging Slice 2, update README/architecture/report docs to use
"Research posture" consistently.

## 2026-06-05 - Slice 2 Ready Subject to Packaging Hygiene

### Decision

Slice 2 is acceptable for review-pack delivery once non-product filesystem
artifacts are removed/ignored.

### Reasoning

The prior functional and safety concerns were addressed: tests pass, Ruff
passes, CLI naming is MIIP-first, research posture replaces action-like
language, policy notes are separated from concentration warnings, and docs
explicitly state manual/static heuristic limits.

### Rejected Alternatives

- Continue broadening Slice 2 scope before review pack.
- Add live data or richer analytics to compensate for heuristic scoring.

### Risks

Packaging clutter such as `.DS_Store` can make the review pack look less
intentional even when product functionality is sound.

### Review Trigger

Before final packaging, run a repository hygiene check for generated files,
OS metadata, caches, and stale review-pack artifacts.
