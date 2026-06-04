from __future__ import annotations

from pathlib import Path

from investment_os.datasource import StaticDataSource
from investment_os.loaders import load_app_config
from investment_os.pipeline import Pipeline
from investment_os.reporting.disclaimer import DISCLAIMER, PLACEHOLDER_NOTICE
from investment_os.reporting.render import render_daily, render_weekly


def _report(config_dir: Path, snapshot_path: Path, report_type: str):
    pipeline = Pipeline(load_app_config(config_dir), StaticDataSource(snapshot_path))
    return pipeline.build_report(
        report_type=report_type, period_label="2026-W23", title="Test report"
    )


def test_daily_includes_disclaimer(config_dir: Path, snapshot_path: Path) -> None:
    md = render_daily(_report(config_dir, snapshot_path, "daily"))
    assert DISCLAIMER in md
    assert PLACEHOLDER_NOTICE in md
    assert "MIIP monitor status" in md
    assert "Investment thesis framing" in md
    assert "Data completeness and provenance" in md
    assert "Macro Risk" in md
    assert "Portfolio Risk" in md
    assert "Overall regime" in md
    assert "Research posture (not advice)" in md
    assert "No action implied" in md
    assert "Possible actions" not in md
    assert "Virtual Investment Committee" in md
    assert "Portfolio concentration warning" in md
    assert "Thesis invalidation" in md
    assert "ZIP.AX" in md


def test_weekly_includes_disclaimer(config_dir: Path, snapshot_path: Path) -> None:
    md = render_weekly(_report(config_dir, snapshot_path, "weekly"))
    assert DISCLAIMER in md
    assert PLACEHOLDER_NOTICE in md
    assert "Summary" in md


def test_review_posture_with_manual_disclaimer(config_dir: Path, snapshot_path: Path) -> None:
    md = render_daily(_report(config_dir, snapshot_path, "daily"))
    idx_posture = md.index("Research posture (not advice)")
    idx_manual = md.index("Manual / static data")
    assert idx_posture < idx_manual


def test_reports_avoid_advice_language(config_dir: Path, snapshot_path: Path) -> None:
    md = render_daily(_report(config_dir, snapshot_path, "daily"))
    lowered = md.lower()
    for banned in ("buy now", "guaranteed", "you should buy", "will rise", "will fall"):
        assert banned not in lowered
