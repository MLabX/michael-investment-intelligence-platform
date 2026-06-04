from __future__ import annotations

from investment_os.agents import MomentumAgent, QualityAgent, RiskAgent, ValueAgent
from investment_os.models import SCORE_NEUTRAL, Instrument, InstrumentMetrics

INSTRUMENT = Instrument(ticker="AAA", name="Alpha", sector="Technology")


def test_momentum_maps_directly() -> None:
    signal = MomentumAgent("momentum").evaluate(INSTRUMENT, InstrumentMetrics(momentum=82))
    assert signal.score == 82
    assert signal.agent == "momentum"
    assert signal.ticker == "AAA"


def test_value_maps_directly() -> None:
    signal = ValueAgent("value").evaluate(INSTRUMENT, InstrumentMetrics(value=35))
    assert signal.score == 35


def test_quality_maps_directly() -> None:
    signal = QualityAgent("quality").evaluate(INSTRUMENT, InstrumentMetrics(quality=78))
    assert signal.score == 78


def test_risk_inverts_volatility() -> None:
    signal = RiskAgent("risk").evaluate(INSTRUMENT, InstrumentMetrics(volatility=60))
    assert signal.score == 40


def test_missing_metric_returns_neutral_with_provenance() -> None:
    signal = MomentumAgent("momentum").evaluate(INSTRUMENT, InstrumentMetrics())
    assert signal.score == SCORE_NEUTRAL
    assert signal.used_neutral_fallback is True
    assert signal.missing_metric == "momentum"


def test_agents_are_deterministic() -> None:
    metrics = InstrumentMetrics(momentum=70)
    a = MomentumAgent("momentum").evaluate(INSTRUMENT, metrics)
    b = MomentumAgent("momentum").evaluate(INSTRUMENT, metrics)
    assert a.score == b.score
