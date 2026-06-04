from __future__ import annotations

from pathlib import Path

import pytest

from investment_os.datasource import ConfigError, StaticDataSource
from investment_os.loaders import load_app_config
from investment_os.monitors import build_monitor_statuses
from investment_os.pipeline import Pipeline


def test_build_monitor_statuses_from_indicators(config_dir: Path, snapshot_path: Path) -> None:
    config = load_app_config(config_dir)
    snapshot = StaticDataSource(snapshot_path).snapshot()
    statuses = build_monitor_statuses(
        config.monitors, config.monitor_scoring, snapshot.monitor_indicators
    )
    assert len(statuses) == 5
    assert all(s.sub_indicators for s in statuses)


def test_data_completeness_warns_on_neutral_agents(config_dir: Path, snapshot_path: Path) -> None:
    text = snapshot_path.read_text(encoding="utf-8")
    text = text.replace("  ZIP.AX:\n    momentum: 80\n", "  ZIP.AX:\n")
    snapshot_path.write_text(text, encoding="utf-8")

    report = Pipeline(load_app_config(config_dir), StaticDataSource(snapshot_path)).build_report(
        report_type="daily", period_label="2026-06-05", title="Daily"
    )
    assert report.data_completeness.neutral_fallback_count >= 1


def test_snapshot_missing_monitor_indicators_rejected(snapshot_path: Path) -> None:
    text = snapshot_path.read_text(encoding="utf-8")
    snapshot_path.write_text(
        text.replace("monitor_indicators:\n", "monitor_indicators_disabled:\n"),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        StaticDataSource(snapshot_path).snapshot()
