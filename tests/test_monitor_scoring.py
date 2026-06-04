from __future__ import annotations

from pathlib import Path

from investment_os.loaders import load_app_config
from investment_os.monitor_scoring import score_monitor


def test_monitor_scoring_weighted_composite() -> None:
    config = load_app_config("config")
    model = config.monitor_scoring["macro_risk"]
    definition = config.monitors["macro_risk"]
    readings = {
        "rates_pressure": 60,
        "liquidity_conditions": 80,
        "credit_stress": 40,
        "market_breadth": 50,
    }
    status = score_monitor("macro_risk", definition, model, readings)
    assert 0 <= status.signal <= 100
    assert len(status.sub_indicators) == 4
    assert status.data_complete


def test_missing_indicator_uses_neutral(config_dir: Path, snapshot_path: Path) -> None:
    from investment_os.datasource import StaticDataSource
    from investment_os.loaders import load_app_config
    from investment_os.monitors import build_monitor_statuses

    config = load_app_config(config_dir)
    snap = StaticDataSource(snapshot_path).snapshot()
    snap.monitor_indicators["macro_risk"] = {"rates_pressure": 50}
    statuses = build_monitor_statuses(
        config.monitors, config.monitor_scoring, snap.monitor_indicators
    )
    macro = next(s for s in statuses if s.monitor_id == "macro_risk")
    assert any(s.used_neutral_fallback for s in macro.sub_indicators)
