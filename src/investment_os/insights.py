"""Virtual Investment Committee and narrative insights (deterministic, no LLM)."""

from __future__ import annotations

from .models import MonitorStatus, PortfolioSummary, VirtualCommitteeView


def build_virtual_committee(
    regime: str,
    monitors: list[MonitorStatus],
    portfolio: PortfolioSummary | None,
) -> VirtualCommitteeView:
    avg_note = (
        f"Overall regime assessed as **{regime}** from mean monitor composite "
        "(manual/static inputs — not live macro data)."
    )
    views: list[str] = []
    for m in monitors:
        subs = ", ".join(f"{s.label} {s.signal:.0f}" for s in m.sub_indicators[:4])
        extra = f" ({subs})" if subs else ""
        views.append(f"- **{m.name}:** signal {m.signal:.0f}, status `{m.status_label}`{extra}.")

    dissent_parts: list[str] = []
    by_id = {m.monitor_id: m for m in monitors}
    ai = by_id.get("ai_capex")
    china = by_id.get("china_rerating")
    if ai and china and ai.signal - china.signal >= 20:
        dissent_parts.append(
            "AI Capex monitor is materially stronger than China Re-rating — "
            "thematic exposure assumptions may conflict."
        )
    macro = by_id.get("macro_risk")
    port = by_id.get("portfolio_risk")
    if macro and port and macro.signal < 50 and port.signal < 50:
        dissent_parts.append(
            "Macro and Portfolio Risk both cautious — equity add ideas face headwinds."
        )
    if portfolio and portfolio.concentration_warnings:
        dissent_parts.append(
            "Portfolio concentration warnings present — size and liquidity views "
            "should be conservative."
        )

    dissent = (
        " ".join(dissent_parts)
        if dissent_parts
        else ("No major cross-monitor dissent flagged on current manual readings.")
    )

    return VirtualCommitteeView(
        chair_summary=avg_note,
        monitor_views=views,
        dissent=dissent,
    )
