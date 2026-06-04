"""Agent base class.

An *agent* turns the metrics for a single instrument into one ``AgentSignal``
on a 0-100 scale. Slice 2 agents are deterministic and read only manual/static
placeholder metrics. When the metric an agent needs is missing, it returns a
neutral score so a partial snapshot never crashes the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SCORE_NEUTRAL, AgentSignal, Instrument, InstrumentMetrics


class Agent(ABC):
    """Base class for all scoring agents."""

    #: Stable type identifier used by the registry / agents.yaml `type` field.
    type_name: str = "base"

    def __init__(self, name: str, params: dict[str, float] | None = None) -> None:
        self.name = name
        self.params = params or {}

    @abstractmethod
    def evaluate(self, instrument: Instrument, metrics: InstrumentMetrics) -> AgentSignal:
        """Return this agent's signal for the given instrument."""

    def _signal(self, instrument: Instrument, score: float, rationale: str) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            ticker=instrument.ticker,
            score=round(float(score), 2),
            rationale=rationale,
            used_neutral_fallback=False,
            missing_metric=None,
        )

    def _neutral(self, instrument: Instrument, missing: str) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            ticker=instrument.ticker,
            score=SCORE_NEUTRAL,
            rationale=(
                f"No '{missing}' metric available; returning neutral {SCORE_NEUTRAL:.0f} "
                "(unknown — not an average observation)."
            ),
            used_neutral_fallback=True,
            missing_metric=missing,
        )
