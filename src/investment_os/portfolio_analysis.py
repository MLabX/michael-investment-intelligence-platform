"""Portfolio loading helpers and concentration analysis."""

from __future__ import annotations

from .models import PortfolioConfig, PortfolioSummary


def analyse_portfolio(portfolio: PortfolioConfig) -> PortfolioSummary:
    invested = sum(h.value_aud for h in portfolio.holdings)
    total = invested + portfolio.cash_aud
    rows: list[dict[str, str | float]] = []
    concentration_warnings: list[str] = []
    policy_notes: list[str] = []
    max_pct = portfolio.risk_constraints.max_single_position_pct

    for holding in portfolio.holdings:
        pct_total = (holding.value_aud / total * 100) if total else 0.0
        pct_invested = (holding.value_aud / invested * 100) if invested else 0.0
        rows.append(
            {
                "ticker": holding.ticker,
                "name": holding.name,
                "value_aud": holding.value_aud,
                "pct_of_total": round(pct_total, 1),
                "pct_of_invested": round(pct_invested, 1),
            }
        )
        if pct_total > max_pct:
            concentration_warnings.append(
                f"{holding.ticker} is {pct_total:.1f}% of total portfolio (AUD {total:,.0f}) "
                f"— exceeds configured maximum {max_pct:.0f}% single-position guideline."
            )
        elif pct_invested > max_pct * 1.5:
            concentration_warnings.append(
                f"{holding.ticker} is {pct_invested:.1f}% of invested capital — high concentration "
                f"relative to cash buffer."
            )

    if portfolio.risk_constraints.mortgages and portfolio.cash_aud < invested * 0.2:
        concentration_warnings.append(
            "Cash buffer is below 20% of invested capital — review mortgage/family "
            "liquidity headroom."
        )

    if portfolio.risk_constraints.avoid_automated_trading:
        policy_notes.append(
            "Automated trading is disabled by policy — MIIP outputs are manual review only."
        )
    if portfolio.risk_constraints.family_responsibilities:
        policy_notes.append("Family responsibilities flagged in portfolio risk constraints.")
    if portfolio.risk_constraints.mortgages:
        policy_notes.append("Mortgage obligations flagged in portfolio risk constraints.")

    return PortfolioSummary(
        owner=portfolio.owner,
        base_currency=portfolio.base_currency,
        cash_aud=portfolio.cash_aud,
        invested_aud=round(invested, 2),
        total_aud=round(total, 2),
        holdings=rows,
        concentration_warnings=concentration_warnings,
        policy_notes=policy_notes,
    )


def derived_portfolio_indicator_readings(
    summary: PortfolioSummary, portfolio: PortfolioConfig
) -> dict[str, float]:
    """Map portfolio structure to 0-100 readings for portfolio_risk monitor indicators."""

    total = summary.total_aud or 1.0
    cash_pct = summary.cash_aud / total * 100
    max_holding_pct = max((float(h["pct_of_total"]) for h in summary.holdings), default=0.0)

    concentration_risk = min(100.0, max_holding_pct * 2.5)
    liquidity_buffer = min(100.0, cash_pct * 2.0)
    headroom = 70.0
    if portfolio.risk_constraints.family_responsibilities:
        headroom -= 10.0
    if portfolio.risk_constraints.mortgages:
        headroom -= 10.0
    if summary.concentration_warnings:
        headroom -= 15.0
    headroom = max(20.0, min(100.0, headroom + liquidity_buffer * 0.2))

    factor_balance = 55.0
    if len(summary.holdings) >= 2:
        factor_balance = 60.0

    return {
        "concentration_risk": round(concentration_risk, 1),
        "factor_balance": round(factor_balance, 1),
        "liquidity_buffer": round(liquidity_buffer, 1),
        "mortgage_family_headroom": round(headroom, 1),
    }
