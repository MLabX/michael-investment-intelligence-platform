"""Shared fixtures: minimal valid MIIP Slice 2 config + data."""

from __future__ import annotations

from pathlib import Path

import pytest

SETTINGS_YAML = """\
default_watchlist: current_holdings
default_scoring_model: balanced
reports_dir: reports
daily_subdir: daily
weekly_subdir: weekly
overall_regime:
  risk_on_min: 65
  balanced_min: 55
  cautious_min: 45
"""

MONITORS_YAML = """\
platform: MIIP
thesis_summary: Test MIIP thesis summary.
monitors:
  macro_risk:
    name: Macro Risk
    thesis: Macro test thesis.
    thesis_invalidation:
      - Macro thesis fails if X.
  ai_capex:
    name: AI Capex
    thesis: AI capex test thesis.
    thesis_invalidation: []
  china_rerating:
    name: China Re-rating
    thesis: China test thesis.
    thesis_invalidation: []
  robotics_physical_ai:
    name: Robotics / Physical AI
    thesis: Robotics test thesis.
    thesis_invalidation: []
  portfolio_risk:
    name: Portfolio Risk
    thesis: Portfolio test thesis.
    thesis_invalidation: []
"""

MONITOR_SCORING_YAML = """\
models:
  macro_risk:
    indicators:
      rates_pressure: {weight: 1.0, higher_is_better: false}
      liquidity_conditions: {weight: 1.0, higher_is_better: true}
  ai_capex:
    indicators:
      capex_momentum: {weight: 1.0, higher_is_better: true}
  china_rerating:
    indicators:
      policy_support: {weight: 1.0, higher_is_better: true}
  robotics_physical_ai:
    indicators:
      adoption_signals: {weight: 1.0, higher_is_better: true}
  portfolio_risk:
    indicators:
      concentration_risk: {weight: 1.0, higher_is_better: false}
      liquidity_buffer: {weight: 1.0, higher_is_better: true}
"""

PORTFOLIO_YAML = """\
owner: Michael
base_currency: AUD
cash_aud: 45000
holdings:
  - ticker: ZIP.AX
    name: Zip Co
    value_aud: 50000
  - ticker: NVX.AX
    name: Novonix
    value_aud: 5000
risk_constraints:
  family_responsibilities: true
  mortgages: true
  max_single_position_pct: 25.0
  avoid_automated_trading: true
"""

WATCHLISTS_YAML = """\
watchlists:
  current_holdings:
    name: current_holdings
    description: Test holdings.
    instruments:
      - ticker: ZIP.AX
        name: Zip Co
        sector: Financials
      - ticker: NVX.AX
        name: Novonix
        sector: Materials
"""

AGENTS_YAML = """\
agents:
  momentum:
    type: momentum
    enabled: true
  value:
    type: value
    enabled: true
  quality:
    type: quality
    enabled: true
  risk:
    type: risk
    enabled: true
"""

SCORING_YAML = """\
default_model: balanced
models:
  balanced:
    description: Equal blend.
    weights:
      momentum: 1.0
      value: 1.0
      quality: 1.0
      risk: 1.0
"""

INDICATORS = """\
  macro_risk:
    rates_pressure: 60
    liquidity_conditions: 55
  ai_capex:
    capex_momentum: 70
  china_rerating:
    policy_support: 40
  robotics_physical_ai:
    adoption_signals: 65
  portfolio_risk:
    concentration_risk: 70
    liquidity_buffer: 55
"""

SNAPSHOT_YAML = f"""\
source: manual-static
as_of: 2026-06-05
placeholder: true
monitor_indicators:
{INDICATORS}
monitors: {{}}
metrics:
  ZIP.AX:
    momentum: 80
    value: 40
    quality: 60
    volatility: 20
  NVX.AX:
    momentum: 40
    value: 60
    quality: 50
    volatility: 80
"""


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    cfg = tmp_path / "config"
    cfg.mkdir()
    for name, content in [
        ("settings.yaml", SETTINGS_YAML),
        ("monitors.yaml", MONITORS_YAML),
        ("monitor_scoring.yaml", MONITOR_SCORING_YAML),
        ("portfolio.yaml", PORTFOLIO_YAML),
        ("watchlists.yaml", WATCHLISTS_YAML),
        ("agents.yaml", AGENTS_YAML),
        ("scoring.yaml", SCORING_YAML),
    ]:
        (cfg / name).write_text(content, encoding="utf-8")
    return cfg


@pytest.fixture
def snapshot_path(tmp_path: Path) -> Path:
    path = tmp_path / "data" / "market_snapshot.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(SNAPSHOT_YAML, encoding="utf-8")
    return path
