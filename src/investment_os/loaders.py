"""Load and cross-validate YAML configuration into typed models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import (
    AgentsConfig,
    AppConfig,
    MonitorsConfig,
    MonitorScoringConfig,
    PortfolioConfig,
    ScoringConfig,
    Settings,
    WatchlistsConfig,
)

DEFAULT_CONFIG_DIR = Path("config")

SETTINGS_FILE = "settings.yaml"
MONITORS_FILE = "monitors.yaml"
MONITOR_SCORING_FILE = "monitor_scoring.yaml"
PORTFOLIO_FILE = "portfolio.yaml"
WATCHLISTS_FILE = "watchlists.yaml"
AGENTS_FILE = "agents.yaml"
SCORING_FILE = "scoring.yaml"


class ConfigError(Exception):
    """Raised when configuration is missing, malformed, or inconsistent."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing configuration file: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:  # pragma: no cover
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if data is None:
        raise ConfigError(f"Configuration file is empty: {path}")
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a mapping at the top level of {path}")
    return data


def load_app_config(config_dir: Path | str = DEFAULT_CONFIG_DIR) -> AppConfig:
    """Load every config file, validate it, and check cross-references."""

    config_dir = Path(config_dir)

    try:
        settings = Settings.model_validate(_read_yaml(config_dir / SETTINGS_FILE))
        monitors = MonitorsConfig.model_validate(_read_yaml(config_dir / MONITORS_FILE))
        monitor_scoring = MonitorScoringConfig.model_validate(
            _read_yaml(config_dir / MONITOR_SCORING_FILE)
        )
        portfolio = PortfolioConfig.model_validate(_read_yaml(config_dir / PORTFOLIO_FILE))
        watchlists = WatchlistsConfig.model_validate(_read_yaml(config_dir / WATCHLISTS_FILE))
        agents = AgentsConfig.model_validate(_read_yaml(config_dir / AGENTS_FILE))
        scoring = ScoringConfig.model_validate(_read_yaml(config_dir / SCORING_FILE))
    except ValidationError as exc:
        raise ConfigError(f"Configuration validation failed:\n{exc}") from exc

    _validate_cross_references(settings, watchlists, agents, scoring, portfolio)

    return AppConfig(
        settings=settings,
        platform=monitors.platform,
        thesis_summary=monitors.thesis_summary.strip(),
        monitors=monitors.monitors,
        monitor_scoring=monitor_scoring.models,
        portfolio=portfolio,
        watchlists=watchlists.watchlists,
        agents=agents.agents,
        scoring_models=scoring.models,
        default_scoring_model=scoring.default_model,
    )


def _validate_cross_references(
    settings: Settings,
    watchlists: WatchlistsConfig,
    agents: AgentsConfig,
    scoring: ScoringConfig,
    portfolio: PortfolioConfig,
) -> None:
    if settings.default_watchlist not in watchlists.watchlists:
        raise ConfigError(
            f"settings.default_watchlist '{settings.default_watchlist}' "
            f"is not defined in {WATCHLISTS_FILE}"
        )

    if settings.default_scoring_model not in scoring.models:
        raise ConfigError(
            f"settings.default_scoring_model '{settings.default_scoring_model}' "
            f"is not defined in {SCORING_FILE}"
        )

    if scoring.default_model not in scoring.models:
        raise ConfigError(
            f"scoring.default_model '{scoring.default_model}' is not a defined scoring model"
        )

    enabled_agents = {name for name, cfg in agents.agents.items() if cfg.enabled}
    for model_name, model in scoring.models.items():
        unknown = set(model.weights) - set(agents.agents)
        if unknown:
            raise ConfigError(
                f"scoring model '{model_name}' references unknown agents: {sorted(unknown)}"
            )
        disabled_with_weight = {
            a for a, w in model.weights.items() if w > 0 and a not in enabled_agents
        }
        if disabled_with_weight:
            raise ConfigError(
                f"scoring model '{model_name}' assigns positive weight to disabled agents: "
                f"{sorted(disabled_with_weight)}"
            )
        contributing = {a for a, w in model.weights.items() if w > 0 and a in enabled_agents}
        if not contributing:
            raise ConfigError(
                f"scoring model '{model_name}' has no enabled agents with positive weight"
            )

    holding_tickers = {h.ticker for h in portfolio.holdings}
    wl = watchlists.watchlists.get("current_holdings")
    if wl:
        wl_tickers = {i.ticker for i in wl.instruments}
        missing = holding_tickers - wl_tickers
        if missing:
            raise ConfigError(
                f"portfolio holdings not in current_holdings watchlist: {sorted(missing)}"
            )
