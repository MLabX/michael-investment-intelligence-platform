from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from investment_os import __version__
from investment_os.cli import app

runner = CliRunner()


def _common(config_dir: Path, snapshot_path: Path) -> list[str]:
    return ["--config-dir", str(config_dir), "--data", str(snapshot_path)]


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_validate_config_ok(config_dir: Path, snapshot_path: Path) -> None:
    result = runner.invoke(app, ["validate-config", *_common(config_dir, snapshot_path)])
    assert result.exit_code == 0
    assert "Configuration OK" in result.stdout


def test_validate_config_fails_on_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate-config", "--config-dir", str(tmp_path)])
    assert result.exit_code == 1


def test_score_outputs_ranked(config_dir: Path, snapshot_path: Path) -> None:
    result = runner.invoke(app, ["score", *_common(config_dir, snapshot_path)])
    assert result.exit_code == 0
    assert "ZIP.AX" in result.stdout
    assert "not financial advice" in result.stdout


def test_report_daily_writes_file(config_dir: Path, snapshot_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "daily.md"
    args = ["report", "daily", *_common(config_dir, snapshot_path)]
    args += ["--date", "2026-06-04", "--out", str(out)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Daily Research Signals - 2026-06-04" in content
    assert "Disclaimer" in content


def test_report_weekly_writes_file(config_dir: Path, snapshot_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "weekly.md"
    args = ["report", "weekly", *_common(config_dir, snapshot_path)]
    args += ["--date", "2026-06-04", "--out", str(out)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    assert "2026-W23" in out.read_text(encoding="utf-8")
