"""Quality agent: higher business quality scores higher."""

from __future__ import annotations

from ..models import AgentSignal, Instrument, InstrumentMetrics
from .base import Agent


class QualityAgent(Agent):
    type_name = "quality"

    def evaluate(self, instrument: Instrument, metrics: InstrumentMetrics) -> AgentSignal:
        if metrics.quality is None:
            return self._neutral(instrument, "quality")
        score = metrics.quality
        return self._signal(
            instrument,
            score,
            f"Quality metric {metrics.quality:.0f}/100 maps directly to the signal.",
        )
