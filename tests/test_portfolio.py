from __future__ import annotations

from pathlib import Path

from investment_os.loaders import load_app_config
from investment_os.portfolio_analysis import analyse_portfolio, derived_portfolio_indicator_readings


def test_load_portfolio_from_repo() -> None:
    config = load_app_config("config")
    assert config.portfolio.owner == "Michael"
    assert config.portfolio.base_currency == "AUD"
    assert config.portfolio.cash_aud == 45000
    tickers = {h.ticker for h in config.portfolio.holdings}
    assert tickers == {"ZIP.AX", "NVX.AX"}


def test_concentration_warning_for_zip(config_dir: Path) -> None:
    config = load_app_config(config_dir)
    summary = analyse_portfolio(config.portfolio)
    assert summary.total_aud == 100_000
    assert any("ZIP.AX" in w for w in summary.concentration_warnings)
    assert not any("Automated trading" in w for w in summary.concentration_warnings)
    assert any("Automated trading" in n for n in summary.policy_notes)


def test_derived_portfolio_indicators(config_dir: Path) -> None:
    config = load_app_config(config_dir)
    summary = analyse_portfolio(config.portfolio)
    readings = derived_portfolio_indicator_readings(summary, config.portfolio)
    assert "concentration_risk" in readings
    assert "liquidity_buffer" in readings
