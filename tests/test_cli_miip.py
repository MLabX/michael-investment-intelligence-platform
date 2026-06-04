from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from investment_os import __version__
from investment_os.cli import app

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def test_console_scripts_defined_in_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert scripts["miip"] == "investment_os.cli:app"
    assert scripts["investment-os"] == "investment_os.cli:app"


def test_investment_os_alias_same_app() -> None:
    from investment_os.cli import app as app2

    assert app is app2


def test_cli_version_shows_miip() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"miip {__version__}"
