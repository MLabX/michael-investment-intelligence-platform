"""MIIP monitor evaluation — delegates to monitor_scoring for Slice 2."""

from __future__ import annotations

from .models import (
    SCORE_NEUTRAL,
    DataCompletenessSummary,
    InstrumentScore,
    MonitorDefinition,
    MonitorScoringModel,
    MonitorStatus,
)
from .monitor_scoring import build_all_monitor_statuses


def build_monitor_statuses(
    monitor_defs: dict[str, MonitorDefinition],
    scoring_models: dict[str, MonitorScoringModel],
    indicator_data: dict[str, dict[str, float]],
    supplemental_by_monitor: dict[str, dict[str, float]] | None = None,
) -> list[MonitorStatus]:
    return build_all_monitor_statuses(
        monitor_defs, scoring_models, indicator_data, supplemental_by_monitor
    )


def build_data_completeness(
    scores: list[InstrumentScore],
    monitor_statuses: list[MonitorStatus],
) -> DataCompletenessSummary:
    """Summarise portfolio vs monitor data gaps separately."""

    portfolio_neutral = sum(s.neutral_signal_count for s in scores)
    monitor_incomplete = sum(1 for m in monitor_statuses if not m.data_complete)
    monitors_total = len(monitor_statuses)
    total_evals = sum(len(s.signals) for s in scores)
    missing_events: list[str] = []
    for score in scores:
        for signal in score.signals:
            if signal.used_neutral_fallback and signal.missing_metric:
                missing_events.append(f"{score.ticker}/{signal.agent}:{signal.missing_metric}")
    for monitor in monitor_statuses:
        for sub in monitor.sub_indicators:
            if sub.used_neutral_fallback:
                missing_events.append(f"{monitor.monitor_id}/{sub.indicator_id}:missing")

    warnings: list[str] = []
    incomplete_ids = [m.monitor_id for m in monitor_statuses if not m.data_complete]
    if incomplete_ids:
        warnings.append(
            "MIIP monitors with incomplete manual readings: " + ", ".join(incomplete_ids)
        )
    if portfolio_neutral:
        warnings.append(
            f"{portfolio_neutral} watchlist agent evaluation(s) used neutral fallback "
            f"({SCORE_NEUTRAL:.0f}) — update manual metrics in data snapshot."
        )
    if monitor_incomplete:
        warnings.append(
            f"{monitor_incomplete} of {monitors_total} monitor(s) have incomplete sub-indicators."
        )

    portfolio_metric_completeness_pct = 100.0
    if total_evals:
        portfolio_metric_completeness_pct = round(100.0 * (1 - portfolio_neutral / total_evals), 1)
    monitor_completeness_pct = (
        round(100.0 * (monitors_total - monitor_incomplete) / monitors_total, 1)
        if monitors_total
        else 100.0
    )

    return DataCompletenessSummary(
        instruments_evaluated=len(scores),
        total_agent_evaluations=total_evals,
        portfolio_neutral_fallback_count=portfolio_neutral,
        monitor_incomplete_count=monitor_incomplete,
        monitors_total=monitors_total,
        neutral_fallback_count=portfolio_neutral + monitor_incomplete,
        portfolio_metric_completeness_pct=portfolio_metric_completeness_pct,
        monitor_completeness_pct=monitor_completeness_pct,
        completeness_pct=portfolio_metric_completeness_pct,
        missing_events=missing_events,
        warnings=warnings,
    )


def aggregate_risk_flags(monitor_statuses: list[MonitorStatus]) -> list[str]:
    seen: set[str] = set()
    flags: list[str] = []
    for monitor in monitor_statuses:
        for flag in monitor.risk_flags:
            if flag not in seen:
                seen.add(flag)
                flags.append(flag)
    return flags


def count_neutral_signals(signals: list) -> int:
    return sum(1 for s in signals if s.used_neutral_fallback)
