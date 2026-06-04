"""Momentum agent: higher recent trend strength scores higher."""

from __future__ import annotations

from ..models import AgentSignal, Instrument, InstrumentMetrics
from .base import Agent


class MomentumAgent(Agent):
    type_name = "momentum"

    def evaluate(self, instrument: Instrument, metrics: InstrumentMetrics) -> AgentSignal:
        if metrics.momentum is None:
            return self._neutral(instrument, "momentum")
        score = metrics.momentum
        return self._signal(
            instrument,
            score,
            f"Momentum metric {metrics.momentum:.0f}/100 maps directly to the signal.",
        )
