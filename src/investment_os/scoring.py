"""Scoring engine: combine per-agent signals into a ranked composite score.

The composite is a weighted average of agent signals using the weights from the
selected :class:`ScoringModel`. Only agents that actually produced a signal and
have a positive weight contribute, and weights are normalised so the composite
stays on the same 0-100 scale. Results are relative research signals, not
predictions or recommendations.
"""

from __future__ import annotations

from .models import AgentSignal, Instrument, InstrumentScore, ScoringModel
from .monitors import count_neutral_signals


def score_instrument(
    instrument: Instrument,
    signals: list[AgentSignal],
    model: ScoringModel,
) -> InstrumentScore:
    """Compute the weighted composite score for a single instrument."""

    weighted_sum = 0.0
    weight_total = 0.0
    for signal in signals:
        weight = model.weights.get(signal.agent, 0.0)
        if weight <= 0:
            continue
        weighted_sum += signal.score * weight
        weight_total += weight

    composite = weighted_sum / weight_total if weight_total > 0 else 0.0

    return InstrumentScore(
        ticker=instrument.ticker,
        name=instrument.name,
        sector=instrument.sector,
        composite=round(composite, 2),
        signals=signals,
        neutral_signal_count=count_neutral_signals(signals),
    )


def rank_scores(scores: list[InstrumentScore]) -> list[InstrumentScore]:
    """Return scores sorted by composite (desc), with ``rank`` populated.

    Ties are broken by ticker so ordering is fully deterministic.
    """

    ordered = sorted(scores, key=lambda s: (-s.composite, s.ticker))
    for index, score in enumerate(ordered, start=1):
        score.rank = index
    return ordered
