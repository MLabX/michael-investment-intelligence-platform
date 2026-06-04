from __future__ import annotations

from investment_os.models import AgentSignal, Instrument, ScoringModel
from investment_os.scoring import rank_scores, score_instrument

INSTRUMENT = Instrument(ticker="AAA", name="Alpha", sector="Technology")


def _signals(**kwargs: float) -> list[AgentSignal]:
    return [AgentSignal(agent=a, ticker="AAA", score=v) for a, v in kwargs.items()]


def test_equal_weights_is_plain_average() -> None:
    model = ScoringModel(weights={"momentum": 1, "value": 1})
    score = score_instrument(INSTRUMENT, _signals(momentum=80, value=40), model)
    assert score.composite == 60.0


def test_weights_are_normalised() -> None:
    model = ScoringModel(weights={"momentum": 3, "value": 1})
    score = score_instrument(INSTRUMENT, _signals(momentum=80, value=40), model)
    assert score.composite == 70.0  # (80*3 + 40*1) / 4


def test_zero_weight_agent_excluded() -> None:
    model = ScoringModel(weights={"momentum": 1, "value": 0})
    score = score_instrument(INSTRUMENT, _signals(momentum=80, value=40), model)
    assert score.composite == 80.0


def test_ranking_is_deterministic_with_tiebreak() -> None:
    model = ScoringModel(weights={"momentum": 1})
    a = score_instrument(Instrument(ticker="ZZZ", name="Z"), _signals(momentum=50), model)
    b = score_instrument(Instrument(ticker="AAA", name="A"), _signals(momentum=50), model)
    c = score_instrument(Instrument(ticker="MMM", name="M"), _signals(momentum=90), model)
    ranked = rank_scores([a, b, c])
    assert [s.ticker for s in ranked] == ["MMM", "AAA", "ZZZ"]
    assert [s.rank for s in ranked] == [1, 2, 3]
