from __future__ import annotations

from datetime import date
from pathlib import Path

from investment_os.datasource import StaticDataSource
from investment_os.loaders import load_app_config
from investment_os.pipeline import Pipeline, iso_week_label


def _pipeline(config_dir: Path, snapshot_path: Path) -> Pipeline:
    return Pipeline(load_app_config(config_dir), StaticDataSource(snapshot_path))


def test_run_ranks_instruments(config_dir: Path, snapshot_path: Path) -> None:
    scores = _pipeline(config_dir, snapshot_path).run()
    assert [s.ticker for s in scores] == ["ZIP.AX", "NVX.AX"]
    assert scores[0].rank == 1
    assert scores[0].composite > scores[1].composite


def test_run_is_deterministic(config_dir: Path, snapshot_path: Path) -> None:
    pipeline = _pipeline(config_dir, snapshot_path)
    first = pipeline.run()
    second = pipeline.run()
    assert [(s.ticker, s.composite) for s in first] == [(s.ticker, s.composite) for s in second]


def test_build_report_carries_provenance(config_dir: Path, snapshot_path: Path) -> None:
    report = _pipeline(config_dir, snapshot_path).build_report(
        report_type="daily",
        period_label="2026-06-04",
        title="Daily",
    )
    assert report.platform == "MIIP"
    assert report.is_placeholder_data is True
    assert report.data_as_of == date(2026, 6, 5)
    assert report.watchlist_name == "current_holdings"
    assert report.overall_regime
    assert report.virtual_committee is not None
    assert report.review_posture
    assert report.scoring_model_name == "balanced"
    assert len(report.monitors) == 5
    assert len(report.scores) == 2


def test_iso_week_label() -> None:
    assert iso_week_label(date(2026, 6, 4)) == "2026-W23"
