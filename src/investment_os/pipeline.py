"""Pipeline orchestrator."""

from __future__ import annotations

from datetime import UTC, date, datetime

from .agents.registry import build_agents
from .datasource import DataSource, StaticDataSource
from .insights import build_virtual_committee
from .loaders import ConfigError
from .models import AppConfig, InstrumentMetrics, InstrumentScore, ReportModel, ScoringModel
from .monitors import aggregate_risk_flags, build_data_completeness, build_monitor_statuses
from .portfolio_analysis import analyse_portfolio, derived_portfolio_indicator_readings
from .regime import classify_overall_regime, suggest_review_posture
from .scoring import rank_scores, score_instrument


class Pipeline:
    """Runs monitors, portfolio analysis, and instrument scoring."""

    def __init__(self, config: AppConfig, data_source: DataSource | None = None) -> None:
        self.config = config
        self.data_source = data_source or StaticDataSource()
        self.agents = build_agents(config.agents)

    def resolve_watchlist(self, name: str | None) -> str:
        return name or self.config.settings.default_watchlist

    def resolve_scoring_model(self, name: str | None) -> str:
        return name or self.config.default_scoring_model

    def _get_scoring_model(self, name: str) -> ScoringModel:
        model = self.config.scoring_models.get(name)
        if model is None:
            raise ConfigError(
                f"Unknown scoring model '{name}'. Available: {sorted(self.config.scoring_models)}"
            )
        return model

    def run(
        self,
        watchlist_name: str | None = None,
        scoring_model_name: str | None = None,
    ) -> list[InstrumentScore]:
        watchlist_name = self.resolve_watchlist(watchlist_name)
        scoring_model_name = self.resolve_scoring_model(scoring_model_name)

        watchlist = self.config.watchlists.get(watchlist_name)
        if watchlist is None:
            raise ConfigError(
                f"Unknown watchlist '{watchlist_name}'. Available: {sorted(self.config.watchlists)}"
            )
        model = self._get_scoring_model(scoring_model_name)

        snapshot = self.data_source.snapshot()
        scores: list[InstrumentScore] = []
        for instrument in watchlist.instruments:
            metrics = snapshot.metrics.get(instrument.ticker) or InstrumentMetrics()
            signals = [agent.evaluate(instrument, metrics) for agent in self.agents]
            scores.append(score_instrument(instrument, signals, model))

        return rank_scores(scores)

    def build_report(
        self,
        report_type: str,
        period_label: str,
        title: str,
        watchlist_name: str | None = None,
        scoring_model_name: str | None = None,
        generated_at: datetime | None = None,
    ) -> ReportModel:
        watchlist_name = self.resolve_watchlist(watchlist_name)
        scoring_model_name = self.resolve_scoring_model(scoring_model_name)
        scores = self.run(watchlist_name, scoring_model_name)
        snapshot = self.data_source.snapshot()

        portfolio_summary = analyse_portfolio(self.config.portfolio)
        supplemental = {
            "portfolio_risk": derived_portfolio_indicator_readings(
                portfolio_summary, self.config.portfolio
            )
        }
        monitor_statuses = build_monitor_statuses(
            self.config.monitors,
            self.config.monitor_scoring,
            snapshot.monitor_indicators,
            supplemental,
        )
        for status in monitor_statuses:
            meta = snapshot.monitors.get(status.monitor_id)
            if meta:
                status.change_drivers = list(meta.change_drivers)
                status.risk_flags = list(dict.fromkeys(status.risk_flags + meta.risk_flags))

        completeness = build_data_completeness(scores, monitor_statuses)
        regime = classify_overall_regime(monitor_statuses, self.config.settings.overall_regime)
        review_posture = suggest_review_posture(
            regime,
            portfolio_summary.concentration_warnings,
            not all(m.data_complete for m in monitor_statuses),
        )
        vic = build_virtual_committee(regime, monitor_statuses, portfolio_summary)

        return ReportModel(
            report_type=report_type,
            title=title,
            period_label=period_label,
            generated_at=generated_at or datetime.now(UTC),
            platform=self.config.platform,
            thesis_summary=self.config.thesis_summary,
            watchlist_name=watchlist_name,
            scoring_model_name=scoring_model_name,
            data_source_label=self.data_source.label,
            data_as_of=snapshot.as_of,
            is_placeholder_data=snapshot.placeholder,
            data_mode=snapshot.source,
            monitors=monitor_statuses,
            data_completeness=completeness,
            aggregate_risk_flags=aggregate_risk_flags(monitor_statuses),
            overall_regime=regime,
            review_posture=review_posture,
            virtual_committee=vic,
            portfolio_summary=portfolio_summary,
            scores=scores,
        )


def iso_week_label(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"
