from __future__ import annotations

from investment_os.datasource import StaticDataSource
from investment_os.loaders import load_app_config
from investment_os.models import MonitorStatus, OverallRegimeThresholds
from investment_os.monitor_scoring import build_all_monitor_statuses
from investment_os.regime import classify_overall_regime, suggest_review_posture


def test_classify_risk_on() -> None:
    monitors = [
        MonitorStatus(
            monitor_id="macro_risk",
            name="Macro",
            thesis="",
            signal=70,
            status_label="ok",
        ),
        MonitorStatus(
            monitor_id="ai_capex",
            name="AI",
            thesis="",
            signal=68,
            status_label="ok",
        ),
    ]
    regime = classify_overall_regime(monitors, OverallRegimeThresholds())
    assert regime == "Risk On"


def test_classify_defensive() -> None:
    monitors = [
        MonitorStatus(monitor_id="a", name="A", thesis="", signal=35, status_label="x"),
    ]
    assert classify_overall_regime(monitors, OverallRegimeThresholds()) == "Defensive"


def test_review_posture_avoids_imperative_trade_language() -> None:
    options = suggest_review_posture("Cautious", ["ZIP concentration"], True)
    assert "No action implied — research only" in options
    assert "Add gradually" not in options
    assert "Reduce risk" not in options


def test_regime_from_repo_snapshot() -> None:
    config = load_app_config("config")
    snap = StaticDataSource("data/market_snapshot.yaml").snapshot()
    statuses = build_all_monitor_statuses(
        config.monitors, config.monitor_scoring, snap.monitor_indicators
    )
    regime = classify_overall_regime(statuses, config.settings.overall_regime)
    assert regime in ("Risk On", "Balanced", "Cautious", "Defensive")
