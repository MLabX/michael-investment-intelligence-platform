# Known Unknowns

Strategic uncertainties, risks, and open questions for MIIP. These should guide
future review and prevent the project from hiding unresolved assumptions behind
implementation progress.

## Product Scope

### Unknown

What is the exact user workflow: daily scan, weekly review, pre-trade check,
portfolio risk meeting, or all of the above?

### Why It Matters

Workflow determines report cadence, alerting, data freshness, UI shape, and the
level of explanation required.

### Review Trigger

Before adding a dashboard or alerting, define the primary recurring workflow.

## Monitor Taxonomy

### Unknown

How should the five MIIP monitor domains map to agents, scoring models,
reports, and data contracts?

### Why It Matters

Without a first-class taxonomy, the platform may remain a generic weighted
ranker rather than a domain-specific intelligence system.

### Review Trigger

Before Slice 2 completion, require at least one monitor domain to be represented
end-to-end.

## Data Sources and Provenance

### Unknown

Which data sources are authoritative enough for macro, capex, China, robotics,
and portfolio risk monitoring?

### Why It Matters

Investment intelligence depends more on source quality, freshness, and
interpretability than on scoring mechanics.

### Review Trigger

Before live ingestion, define source priority, update frequency, failure modes,
and provenance fields.

## Historical Persistence

### Unknown

What history must be persisted: raw observations, normalized metrics, agent
signals, composite scores, generated reports, or all of these?

### Why It Matters

Week-over-week analysis, trend detection, reproducibility, and auditability need
different storage choices.

### Review Trigger

Before implementing weekly comparisons, choose the persistence boundary.

## Scoring Semantics

### Unknown

Can a single 0-100 "higher is better" score represent macro risk, AI capex
momentum, China re-rating, robotics adoption, and portfolio risk without
distorting meaning?

### Why It Matters

Some domains may require direction, confidence, velocity, horizon, and severity,
not only attractiveness.

### Review Trigger

When adding domain agents, test whether scalar scores are still sufficient.

## Missing Data Policy

### Unknown

Should missing data be neutral, penalized, excluded, or surfaced as a separate
confidence/completeness signal?

### Why It Matters

Neutral defaults are convenient for Slice 1 but can create false confidence in
real reports.

### Review Trigger

Before using real data, add explicit completeness reporting and decide how
missingness affects scores.

## Portfolio Data Boundary

### Unknown

Will MIIP ingest personal holdings, broker exports, manually entered positions,
or only watchlists?

### Why It Matters

Portfolio holdings introduce privacy, security, personal suitability, and
financial-advice boundary risks.

### Review Trigger

Before adding holdings, define data handling, retention, and compliance language.

## LLM Role

### Unknown

Will LLMs be used for summarization, research retrieval, thesis comparison,
agent scoring, or report prose?

### Why It Matters

LLMs are useful for synthesis but risky for unsupported claims, hallucinated
causality, and blurred provenance.

### Review Trigger

Before adding LLM output, require citation/provenance rules and a distinction
between computed signals and generated narrative.

## Evaluation Standard

### Unknown

How will MIIP know whether it is useful: prediction accuracy, risk avoidance,
decision quality, time saved, reduced blind spots, or thesis discipline?

### Why It Matters

Without an evaluation standard, the system may optimize for polished reports
rather than better investment process.

### Review Trigger

Before expanding beyond Slice 2, define success criteria for the platform.

## Monitor Completeness Semantics

### Unknown

Does a monitor count as complete when a scalar signal is present, or only when
required source observations, evidence, freshness, and confidence fields are
present?

### Why It Matters

Reports currently distinguish missing scalar signals from present signals, but
real investment intelligence will need stronger provenance semantics.

### Review Trigger

Before live monitor data is introduced, define completeness requirements per
monitor domain.

## Partial Monitor Snapshots

### Unknown

Should a snapshot missing an entire monitor domain be invalid, or should the
pipeline emit a neutral/incomplete status for that monitor?

### Why It Matters

Strict validation protects the MIIP taxonomy, but partial ingestion is common in
real data systems. The project needs to choose whether monitor absence is a
contract violation or a reportable data gap.

### Review Trigger

When replacing the static snapshot with live or multi-source ingestion, decide
the validation boundary.

## Research Posture Boundary (formerly “Possible Actions”)

### Unknown

How directive should MIIP research posture language be allowed to become?

### Why It Matters

Imperative phrases (e.g. “reduce risk”, “add gradually”) can read like trade guidance,
especially when paired with a personal portfolio. Slice 2 uses non-prescriptive labels.

### Review Trigger

Before review-pack delivery, ensure research posture options are clearly non-prescriptive
and do not imply a recommendation to trade.

## Portfolio Risk Model Adequacy

### Unknown

What minimum portfolio risk model is acceptable before relying on MIIP for real
portfolio review?

### Why It Matters

Slice 2 concentration analysis is a good heuristic, but it does not model
correlation, sector/geography/factor overlap, liquidity, tax, time horizon, or
personal balance-sheet constraints beyond simple flags.

### Review Trigger

Before Slice 3 expands portfolio workflows, define whether portfolio risk needs
holdings metadata, scenario analysis, or factor exposure modelling.

## Review Pack Terminology Alignment

### Unknown

Will external reviewers expect the original Slice 2 phrase "Possible Actions",
or accept "Research posture (not advice)"?

### Why It Matters

The safer report language reduces advice risk. `docs/SLICE2-ACCEPTANCE.md` maps
“possible actions” checklist items to the research posture section.

### Review Trigger

Before final Slice 2 review-pack delivery, align terminology across docs,
tests, and generated report examples.
