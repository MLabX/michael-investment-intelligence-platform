"""Overall MIIP regime classification from monitor composites."""

from __future__ import annotations

from .models import (
    REGIME_LABELS,
    REVIEW_POSTURE_OPTIONS,
    MonitorStatus,
    OverallRegimeThresholds,
)


def mean_monitor_signal(monitors: list[MonitorStatus]) -> float:
    if not monitors:
        return 50.0
    return sum(m.signal for m in monitors) / len(monitors)


def classify_overall_regime(
    monitors: list[MonitorStatus],
    thresholds: OverallRegimeThresholds,
) -> str:
    """Return one of: Risk On, Balanced, Cautious, Defensive."""

    avg = mean_monitor_signal(monitors)
    if avg >= thresholds.risk_on_min:
        return REGIME_LABELS[0]
    if avg >= thresholds.balanced_min:
        return REGIME_LABELS[1]
    if avg >= thresholds.cautious_min:
        return REGIME_LABELS[2]
    return REGIME_LABELS[3]


def suggest_review_posture(
    regime: str,
    concentration_warnings: list[str],
    data_incomplete: bool,
) -> list[str]:
    """Descriptive research posture menu — not trade or allocation advice."""

    options: list[str] = []
    if concentration_warnings:
        options.append("Review sizing and concentration")
        options.append("No action implied — research only")
    if data_incomplete:
        options.append("No action implied — research only")
        options.append("Defer — refresh manual inputs")

    if regime == "Risk On":
        options.extend(["Further desk research", "Maintain current posture"])
    elif regime == "Balanced":
        options.extend(["Maintain current posture", "No action implied — research only"])
    elif regime == "Cautious":
        options.extend(
            [
                "Maintain current posture",
                "Review sizing and concentration",
                "No action implied — research only",
                "Defer — refresh manual inputs",
            ]
        )
    else:
        options.extend(
            [
                "Review sizing and concentration",
                "Defer — refresh manual inputs",
                "No action implied — research only",
            ]
        )

    seen: set[str] = set()
    ordered: list[str] = []
    for option in options:
        if option in REVIEW_POSTURE_OPTIONS and option not in seen:
            seen.add(option)
            ordered.append(option)
    return ordered or ["No action implied — research only"]


# Backward-compatible alias
suggest_possible_actions = suggest_review_posture
