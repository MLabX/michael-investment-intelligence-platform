"""Risk agent: lower volatility scores higher (risk is inverted volatility).

Higher signal = lower assessed risk, so it composes consistently with the other
agents where "higher is better".
"""

from __future__ import annotations

from ..models import SCORE_MAX, AgentSignal, Instrument, InstrumentMetrics
from .base import Agent


class RiskAgent(Agent):
    type_name = "risk"

    def evaluate(self, instrument: Instrument, metrics: InstrumentMetrics) -> AgentSignal:
        if metrics.volatility is None:
            return self._neutral(instrument, "volatility")
        score = SCORE_MAX - metrics.volatility
        return self._signal(
            instrument,
            score,
            f"Volatility {metrics.volatility:.0f}/100 inverted to a risk signal of {score:.0f}.",
        )
