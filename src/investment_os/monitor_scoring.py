"""Score MIIP monitors from configurable sub-indicators and manual readings."""

from __future__ import annotations

from .models import (
    MIIP_MONITOR_IDS,
    SCORE_MAX,
    SCORE_MIN,
    SCORE_NEUTRAL,
    MonitorDefinition,
    MonitorScoringModel,
    MonitorStatus,
    SubIndicatorScore,
)


def _indicator_signal(raw: float | None, higher_is_better: bool) -> tuple[float, bool]:
    if raw is None:
        return SCORE_NEUTRAL, True
    if not (SCORE_MIN <= raw <= SCORE_MAX):
        raw = max(SCORE_MIN, min(SCORE_MAX, raw))
    signal = raw if higher_is_better else SCORE_MAX - raw
    return round(signal, 2), False


def score_monitor(
    monitor_id: str,
    definition: MonitorDefinition,
    model: MonitorScoringModel,
    readings: dict[str, float],
    supplemental: dict[str, float] | None = None,
) -> MonitorStatus:
    """Compute composite monitor signal from weighted sub-indicators."""

    merged = dict(readings)
    if supplemental:
        merged.update(supplemental)

    sub_scores: list[SubIndicatorScore] = []
    weighted_sum = 0.0
    weight_total = 0.0
    neutral_count = 0

    for ind_id, ind_def in model.indicators.items():
        raw = merged.get(ind_id)
        signal, neutral = _indicator_signal(raw, ind_def.higher_is_better)
        if neutral:
            neutral_count += 1
        sub_scores.append(
            SubIndicatorScore(
                indicator_id=ind_id,
                label=ind_def.label or ind_id,
                raw_reading=raw,
                signal=signal,
                weight=ind_def.weight,
                used_neutral_fallback=neutral,
            )
        )
        weighted_sum += signal * ind_def.weight
        weight_total += ind_def.weight

    composite = weighted_sum / weight_total if weight_total else SCORE_NEUTRAL
    status_label = _status_from_thresholds(composite, model.status_thresholds)
    data_complete = neutral_count == 0
    used_fallback = neutral_count > 0

    risk_flags: list[str] = []
    if used_fallback:
        risk_flags.append(
            f"{neutral_count} sub-indicator(s) missing — neutral {SCORE_NEUTRAL:.0f} "
            "used (not average)."
        )

    return MonitorStatus(
        monitor_id=monitor_id,
        name=definition.name,
        thesis=definition.thesis.strip(),
        signal=round(composite, 2),
        status_label=status_label,
        sub_indicators=sub_scores,
        thesis_invalidation=list(definition.thesis_invalidation),
        data_complete=data_complete,
        used_neutral_fallback=used_fallback,
        risk_flags=risk_flags,
    )


def _status_from_thresholds(composite: float, thresholds: dict[str, float]) -> str:
    if not thresholds:
        if composite >= 65:
            return "constructive"
        if composite >= 55:
            return "balanced"
        if composite >= 45:
            return "cautious"
        return "defensive"

    ordered = sorted(thresholds.items(), key=lambda x: x[1])
    label = ordered[0][0]
    for name, bound in ordered:
        if composite >= bound:
            label = name
    return label


def build_all_monitor_statuses(
    monitor_defs: dict[str, MonitorDefinition],
    scoring_models: dict[str, MonitorScoringModel],
    indicator_data: dict[str, dict[str, float]],
    supplemental_by_monitor: dict[str, dict[str, float]] | None = None,
) -> list[MonitorStatus]:
    statuses: list[MonitorStatus] = []
    supplemental_by_monitor = supplemental_by_monitor or {}
    for monitor_id in MIIP_MONITOR_IDS:
        statuses.append(
            score_monitor(
                monitor_id,
                monitor_defs[monitor_id],
                scoring_models[monitor_id],
                indicator_data.get(monitor_id, {}),
                supplemental_by_monitor.get(monitor_id),
            )
        )
    return statuses
