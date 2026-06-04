from __future__ import annotations

from pathlib import Path

import pytest

from investment_os.loaders import ConfigError, load_app_config


def test_load_valid_config(config_dir: Path) -> None:
    config = load_app_config(config_dir)
    assert "current_holdings" in config.watchlists
    assert config.default_scoring_model == "balanced"
    assert config.settings.default_watchlist == "current_holdings"
    assert {"momentum", "value", "quality", "risk"} <= set(config.agents)


def test_ships_with_valid_repo_config() -> None:
    """The real config/ + data shipped in the repo must be valid."""

    config = load_app_config("config")
    assert config.platform == "MIIP"
    assert len(config.monitors) == 5
    assert "current_holdings" in config.watchlists
    assert config.portfolio.cash_aud == 45000


def test_scoring_disabled_agent_with_positive_weight_rejected(config_dir: Path) -> None:
    (config_dir / "agents.yaml").write_text(
        "agents:\n  momentum:\n    type: momentum\n    enabled: false\n"
        "  value:\n    type: value\n    enabled: true\n",
        encoding="utf-8",
    )
    (config_dir / "scoring.yaml").write_text(
        "default_model: balanced\nmodels:\n  balanced:\n    weights:\n"
        "      momentum: 1.0\n      value: 0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="disabled agents"):
        load_app_config(config_dir)


def test_scoring_no_contributing_enabled_agents_rejected(config_dir: Path) -> None:
    """Positive weights only on disabled agents; enabled agents all weight zero."""
    (config_dir / "agents.yaml").write_text(
        "agents:\n  momentum:\n    type: momentum\n    enabled: true\n"
        "  value:\n    type: value\n    enabled: false\n"
        "  quality:\n    type: quality\n    enabled: false\n"
        "  risk:\n    type: risk\n    enabled: false\n",
        encoding="utf-8",
    )
    (config_dir / "scoring.yaml").write_text(
        "default_model: balanced\nmodels:\n  balanced:\n    weights:\n"
        "      momentum: 0.0\n      value: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="disabled agents"):
        load_app_config(config_dir)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Missing configuration file"):
        load_app_config(tmp_path)


def test_unknown_default_watchlist(config_dir: Path) -> None:
    (config_dir / "settings.yaml").write_text(
        "default_watchlist: nope\ndefault_scoring_model: balanced\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="default_watchlist"):
        load_app_config(config_dir)


def test_scoring_references_unknown_agent(config_dir: Path) -> None:
    (config_dir / "scoring.yaml").write_text(
        "default_model: balanced\nmodels:\n  balanced:\n    weights:\n      mystery: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="unknown agents"):
        load_app_config(config_dir)


def test_extra_key_is_rejected(config_dir: Path) -> None:
    (config_dir / "settings.yaml").write_text(
        "default_watchlist: core\ndefault_scoring_model: balanced\nbogus: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_app_config(config_dir)
