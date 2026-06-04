"""Value agent: higher value attractiveness scores higher."""

from __future__ import annotations

from ..models import AgentSignal, Instrument, InstrumentMetrics
from .base import Agent


class ValueAgent(Agent):
    type_name = "value"

    def evaluate(self, instrument: Instrument, metrics: InstrumentMetrics) -> AgentSignal:
        if metrics.value is None:
            return self._neutral(instrument, "value")
        score = metrics.value
        return self._signal(
            instrument,
            score,
            f"Value metric {metrics.value:.0f}/100 maps directly to the signal.",
        )
