"""Pydantic v2 models for configuration and runtime data.

These models are the single source of truth for the shape of every config file,
the static data snapshot, and the intermediate/runtime objects that flow through
the pipeline. MIIP (Michael Investment Intelligence Platform) is organised around
five investment-monitor domains; factor-style agents under Portfolio Risk are a
Slice 2: factor agents score watchlist instruments from manual metrics; monitors use sub-indicators.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Score bounds used consistently across agents and the scoring engine.
SCORE_MIN = 0.0
SCORE_MAX = 100.0
SCORE_NEUTRAL = 50.0

# MIIP's five first-class investment-monitor domains (config + reports + data).
MIIP_MONITOR_IDS: tuple[str, ...] = (
    "macro_risk",
    "ai_capex",
    "china_rerating",
    "robotics_physical_ai",
    "portfolio_risk",
)


class _Strict(BaseModel):
    """Base model that forbids unknown keys so config typos fail loudly."""

    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# Configuration models (config/*.yaml)
# --------------------------------------------------------------------------- #
class Instrument(_Strict):
    ticker: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sector: str = "Unknown"


class Watchlist(_Strict):
    name: str = Field(..., min_length=1)
    description: str = ""
    instruments: list[Instrument] = Field(default_factory=list)

    @field_validator("instruments")
    @classmethod
    def _non_empty(cls, value: list[Instrument]) -> list[Instrument]:
        if not value:
            raise ValueError("a watchlist must contain at least one instrument")
        return value


class WatchlistsConfig(_Strict):
    watchlists: dict[str, Watchlist]

    @field_validator("watchlists")
    @classmethod
    def _non_empty(cls, value: dict[str, Watchlist]) -> dict[str, Watchlist]:
        if not value:
            raise ValueError("at least one watchlist must be defined")
        return value


class AgentConfig(_Strict):
    type: str = Field(..., min_length=1)
    enabled: bool = True
    params: dict[str, float] = Field(default_factory=dict)


class AgentsConfig(_Strict):
    agents: dict[str, AgentConfig]

    @field_validator("agents")
    @classmethod
    def _non_empty(cls, value: dict[str, AgentConfig]) -> dict[str, AgentConfig]:
        if not value:
            raise ValueError("at least one agent must be defined")
        return value


class ScoringModel(_Strict):
    description: str = ""
    weights: dict[str, float]

    @field_validator("weights")
    @classmethod
    def _valid_weights(cls, value: dict[str, float]) -> dict[str, float]:
        if not value:
            raise ValueError("a scoring model must define at least one weight")
        if any(w < 0 for w in value.values()):
            raise ValueError("scoring weights must be non-negative")
        if sum(value.values()) <= 0:
            raise ValueError("scoring weights must sum to a positive number")
        return value


class ScoringConfig(_Strict):
    default_model: str = Field(..., min_length=1)
    models: dict[str, ScoringModel]

    @field_validator("models")
    @classmethod
    def _non_empty(cls, value: dict[str, ScoringModel]) -> dict[str, ScoringModel]:
        if not value:
            raise ValueError("at least one scoring model must be defined")
        return value


class OverallRegimeThresholds(_Strict):
    """Bounds for classifying overall MIIP regime from mean monitor composite."""

    risk_on_min: float = 65.0
    balanced_min: float = 55.0
    cautious_min: float = 45.0

    @field_validator("risk_on_min", "balanced_min", "cautious_min")
    @classmethod
    def _in_range(cls, v: float) -> float:
        if not (SCORE_MIN <= v <= SCORE_MAX):
            raise ValueError(f"threshold must be between {SCORE_MIN} and {SCORE_MAX}")
        return v


class MonitorDefinition(_Strict):
    """One MIIP investment-monitor domain (thesis + display metadata)."""

    name: str = Field(..., min_length=1)
    thesis: str = ""
    thesis_invalidation: list[str] = Field(default_factory=list)


class MonitorsConfig(_Strict):
    platform: str = "MIIP"
    thesis_summary: str = ""
    monitors: dict[str, MonitorDefinition]

    @field_validator("monitors")
    @classmethod
    def _has_all_miip_monitors(
        cls, value: dict[str, MonitorDefinition]
    ) -> dict[str, MonitorDefinition]:
        missing = set(MIIP_MONITOR_IDS) - set(value)
        if missing:
            raise ValueError(f"MIIP requires monitors: {sorted(missing)}")
        return value


class MonitorIndicatorDef(_Strict):
    label: str = ""
    weight: float = 1.0
    higher_is_better: bool = True

    @field_validator("weight")
    @classmethod
    def _positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("indicator weight must be positive")
        return v


class MonitorScoringModel(_Strict):
    description: str = ""
    indicators: dict[str, MonitorIndicatorDef]
    status_thresholds: dict[str, float] = Field(default_factory=dict)

    @field_validator("indicators")
    @classmethod
    def _non_empty(cls, value: dict[str, MonitorIndicatorDef]) -> dict[str, MonitorIndicatorDef]:
        if not value:
            raise ValueError("monitor scoring model must define at least one indicator")
        return value


class MonitorScoringConfig(_Strict):
    models: dict[str, MonitorScoringModel]

    @field_validator("models")
    @classmethod
    def _has_all_miip_monitors(
        cls, value: dict[str, MonitorScoringModel]
    ) -> dict[str, MonitorScoringModel]:
        missing = set(MIIP_MONITOR_IDS) - set(value)
        if missing:
            raise ValueError(f"monitor scoring must define all MIIP monitors: {sorted(missing)}")
        return value


class Holding(_Strict):
    ticker: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    market: str = "ASX"
    value_aud: float = Field(..., gt=0)


class RiskConstraints(_Strict):
    family_responsibilities: bool = True
    mortgages: bool = True
    max_single_position_pct: float = Field(25.0, ge=0, le=100)
    avoid_automated_trading: bool = True
    notes: list[str] = Field(default_factory=list)


class PortfolioConfig(_Strict):
    owner: str = "Michael"
    base_currency: str = "AUD"
    cash_aud: float = Field(..., ge=0)
    holdings: list[Holding] = Field(default_factory=list)
    risk_constraints: RiskConstraints = Field(default_factory=RiskConstraints)

    @field_validator("holdings")
    @classmethod
    def _non_empty(cls, value: list[Holding]) -> list[Holding]:
        if not value:
            raise ValueError("portfolio must include at least one holding")
        return value


class Settings(_Strict):
    default_watchlist: str = Field(..., min_length=1)
    default_scoring_model: str = Field(..., min_length=1)
    reports_dir: str = "reports"
    daily_subdir: str = "daily"
    weekly_subdir: str = "weekly"
    overall_regime: OverallRegimeThresholds = Field(default_factory=OverallRegimeThresholds)


class AppConfig(_Strict):
    """The fully-loaded, cross-validated application configuration."""

    settings: Settings
    platform: str
    thesis_summary: str
    monitors: dict[str, MonitorDefinition]
    monitor_scoring: dict[str, MonitorScoringModel]
    portfolio: PortfolioConfig
    watchlists: dict[str, Watchlist]
    agents: dict[str, AgentConfig]
    scoring_models: dict[str, ScoringModel]
    default_scoring_model: str


# --------------------------------------------------------------------------- #
# Static data models (data/*.yaml)
# --------------------------------------------------------------------------- #
class MonitorReading(_Strict):
    """Placeholder monitor-level reading (platform-wide, not per ticker)."""

    signal: float | None = None
    status: str = "unknown"
    change_drivers: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator("signal")
    @classmethod
    def _signal_in_range(cls, v: float | None) -> float | None:
        if v is not None and not (SCORE_MIN <= v <= SCORE_MAX):
            raise ValueError(f"monitor signal must be between {SCORE_MIN} and {SCORE_MAX}")
        return v


class InstrumentMetrics(_Strict):
    """Placeholder instrument metrics used by Portfolio Risk factor agents.

    All metrics are expressed on a 0-100 scale where higher is "more" of the
    named attribute. These are NOT real market figures (see data/ notice).
    """

    momentum: float | None = None
    value: float | None = None
    quality: float | None = None
    volatility: float | None = None

    @field_validator("momentum", "value", "quality", "volatility")
    @classmethod
    def _in_range(cls, v: float | None) -> float | None:
        if v is not None and not (SCORE_MIN <= v <= SCORE_MAX):
            raise ValueError(f"metric must be between {SCORE_MIN} and {SCORE_MAX}")
        return v


class MarketSnapshot(_Strict):
    """Manual/static snapshot: monitor indicator readings + instrument metrics."""

    source: str = "manual-static"
    as_of: date
    placeholder: bool = True
    monitors: dict[str, MonitorReading] = Field(default_factory=dict)
    monitor_indicators: dict[str, dict[str, float]] = Field(default_factory=dict)
    metrics: dict[str, InstrumentMetrics] = Field(default_factory=dict)

    @field_validator("monitor_indicators")
    @classmethod
    def _has_miip_indicator_sets(
        cls, value: dict[str, dict[str, float]]
    ) -> dict[str, dict[str, float]]:
        missing = set(MIIP_MONITOR_IDS) - set(value)
        if missing:
            raise ValueError(f"snapshot must include monitor_indicators for: {sorted(missing)}")
        return value


# --------------------------------------------------------------------------- #
# Runtime models (produced by the pipeline)
# --------------------------------------------------------------------------- #
class AgentSignal(BaseModel):
    agent: str
    ticker: str
    score: float = Field(..., ge=SCORE_MIN, le=SCORE_MAX)
    rationale: str = ""
    used_neutral_fallback: bool = False
    missing_metric: str | None = None


class InstrumentScore(BaseModel):
    ticker: str
    name: str
    sector: str
    composite: float = Field(..., ge=SCORE_MIN, le=SCORE_MAX)
    rank: int = 0
    signals: list[AgentSignal] = Field(default_factory=list)
    neutral_signal_count: int = 0


class SubIndicatorScore(BaseModel):
    indicator_id: str
    label: str
    raw_reading: float | None = None
    signal: float = Field(..., ge=SCORE_MIN, le=SCORE_MAX)
    weight: float
    used_neutral_fallback: bool = False


class MonitorStatus(BaseModel):
    """Runtime status for one MIIP monitor domain."""

    monitor_id: str
    name: str
    thesis: str
    signal: float = Field(..., ge=SCORE_MIN, le=SCORE_MAX)
    status_label: str
    sub_indicators: list[SubIndicatorScore] = Field(default_factory=list)
    change_drivers: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    thesis_invalidation: list[str] = Field(default_factory=list)
    data_complete: bool = True
    used_neutral_fallback: bool = False


class PortfolioSummary(BaseModel):
    owner: str
    base_currency: str
    cash_aud: float
    invested_aud: float
    total_aud: float
    holdings: list[dict[str, str | float]]
    concentration_warnings: list[str] = Field(default_factory=list)
    policy_notes: list[str] = Field(default_factory=list)


class VirtualCommitteeView(BaseModel):
    chair_summary: str
    monitor_views: list[str] = Field(default_factory=list)
    dissent: str = ""


REGIME_LABELS: tuple[str, ...] = ("Risk On", "Balanced", "Cautious", "Defensive")

# Research posture labels — descriptive, not trade instructions.
REVIEW_POSTURE_OPTIONS: tuple[str, ...] = (
    "Further desk research",
    "Maintain current posture",
    "Review sizing and concentration",
    "No action implied — research only",
    "Defer — refresh manual inputs",
)

# Backward-compatible alias for tests/modules that imported ACTION_OPTIONS.
ACTION_OPTIONS = REVIEW_POSTURE_OPTIONS


class DataCompletenessSummary(BaseModel):
    """Provenance and completeness warnings so neutral scores are not silent."""

    instruments_evaluated: int = 0
    total_agent_evaluations: int = 0
    portfolio_neutral_fallback_count: int = 0
    monitor_incomplete_count: int = 0
    monitors_total: int = 0
    neutral_fallback_count: int = 0
    portfolio_metric_completeness_pct: float = 100.0
    monitor_completeness_pct: float = 100.0
    completeness_pct: float = 100.0
    missing_events: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReportModel(BaseModel):
    """Everything a renderer needs to produce a report. Pure data, no I/O."""

    report_type: str
    title: str
    period_label: str
    generated_at: datetime
    platform: str = "MIIP"
    thesis_summary: str = ""
    watchlist_name: str
    scoring_model_name: str
    data_source_label: str
    data_as_of: date
    is_placeholder_data: bool
    data_mode: str = "manual-static"
    monitors: list[MonitorStatus] = Field(default_factory=list)
    data_completeness: DataCompletenessSummary = Field(default_factory=DataCompletenessSummary)
    aggregate_risk_flags: list[str] = Field(default_factory=list)
    overall_regime: str = "Balanced"
    review_posture: list[str] = Field(default_factory=list)
    virtual_committee: VirtualCommitteeView | None = None
    portfolio_summary: PortfolioSummary | None = None
    scores: list[InstrumentScore] = Field(default_factory=list)
