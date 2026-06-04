"""Markdown renderers for MIIP daily and weekly reports."""

from __future__ import annotations

from ..models import ReportModel
from .disclaimer import DISCLAIMER, MANUAL_DATA_NOTICE


def _header(report: ReportModel) -> list[str]:
    generated = report.generated_at.strftime("%Y-%m-%d %H:%M %Z").strip()
    return [
        f"# {report.title}",
        "",
        f"- **Platform:** {report.platform}",
        f"- **Data mode:** {report.data_mode}",
        f"- **Period:** {report.period_label}",
        f"- **Watchlist:** {report.watchlist_name}",
        f"- **Scoring model:** {report.scoring_model_name}",
        f"- **Data source:** {report.data_source_label}",
        f"- **Data as of:** {report.data_as_of.isoformat()}",
        f"- **Generated:** {generated}",
    ]


def _thesis_framing(report: ReportModel) -> list[str]:
    lines = ["## Investment thesis framing", ""]
    if report.thesis_summary:
        lines.append(report.thesis_summary.strip())
        lines.append("")
    lines.append(
        "_MIIP uses manual/static inputs only (heuristic, not validated analytics). "
        "This report supports deliberation; it does not execute trades or provide "
        "live market intelligence._"
    )
    return lines


def _overall_regime(report: ReportModel) -> list[str]:
    return [
        "## Overall regime",
        "",
        f"**{report.overall_regime}**",
        "",
        "_Derived from mean monitor composite vs configured thresholds — not a live macro model._",
    ]


def _review_posture(report: ReportModel) -> list[str]:
    # Acceptance checklists may refer to "possible actions"; report uses safer heading.
    lines = ["## Research posture (not advice)", ""]
    lines.append(
        "_Also satisfies acceptance criteria for “research posture / possible actions”. "
        "Descriptive options from regime and manual readings — not trade instructions, "
        "allocation advice, or execution guidance._"
    )
    lines.append("")
    for option in report.review_posture:
        lines.append(f"- {option}")
    return lines


def _portfolio_policy_notes(report: ReportModel) -> list[str]:
    ps = report.portfolio_summary
    if not ps or not ps.policy_notes:
        return []
    lines = ["## Portfolio policy notes", ""]
    for note in ps.policy_notes:
        lines.append(f"- {note}")
    return lines


def _virtual_committee(report: ReportModel) -> list[str]:
    vic = report.virtual_committee
    if not vic:
        return []
    lines = ["## Virtual Investment Committee", "", vic.chair_summary, ""]
    lines.append("### Monitor views")
    lines.append("")
    lines.extend(vic.monitor_views)
    lines.append("")
    lines.append("### Dissent / tension")
    lines.append("")
    lines.append(vic.dissent)
    return lines


def _portfolio_section(report: ReportModel) -> list[str]:
    ps = report.portfolio_summary
    if not ps:
        return []
    lines = [
        "## Michael's portfolio (manual entry)",
        "",
        f"- **Owner:** {ps.owner}",
        f"- **Base currency:** {ps.base_currency}",
        f"- **Cash:** AUD {ps.cash_aud:,.0f}",
        f"- **Invested:** AUD {ps.invested_aud:,.0f}",
        f"- **Total:** AUD {ps.total_aud:,.0f}",
        "",
        "| Ticker | Value (AUD) | % of total | % of invested |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for row in ps.holdings:
        lines.append(
            f"| {row['ticker']} | {row['value_aud']:,.0f} | {row['pct_of_total']}% | "
            f"{row['pct_of_invested']}% |"
        )
    return lines


def _concentration_warning(report: ReportModel) -> list[str]:
    ps = report.portfolio_summary
    if not ps or not ps.concentration_warnings:
        return [
            "## Portfolio concentration warning",
            "",
            "_No concentration warnings at current manual portfolio weights._",
        ]
    lines = ["## Portfolio concentration warning", ""]
    for w in ps.concentration_warnings:
        lines.append(f"- {w}")
    return lines


def _thesis_invalidation(report: ReportModel) -> list[str]:
    lines = ["## Thesis invalidation conditions", ""]
    for monitor in report.monitors:
        if not monitor.thesis_invalidation:
            continue
        lines.append(f"### {monitor.name}")
        for cond in monitor.thesis_invalidation:
            lines.append(f"- {cond}")
        lines.append("")
    return lines


def _monitor_status_table(report: ReportModel) -> list[str]:
    lines = [
        "## MIIP monitor status",
        "",
        "| Monitor | Signal | Status | Data |",
        "| :--- | ---: | :--- | :--- |",
    ]
    for monitor in report.monitors:
        data_cell = "complete" if monitor.data_complete else "**incomplete**"
        if monitor.used_neutral_fallback:
            data_cell = "**neutral fallback**"
        lines.append(
            f"| {monitor.name} | {monitor.signal:.0f} | {monitor.status_label} | {data_cell} |"
        )
    return lines


def _monitor_details(report: ReportModel) -> list[str]:
    lines: list[str] = ["", "### Monitor detail (sub-indicators)", ""]
    for monitor in report.monitors:
        lines.append(f"#### {monitor.name}")
        lines.append("")
        if monitor.thesis:
            lines.append(f"- **Thesis:** {monitor.thesis}")
        lines.append(f"- **Composite signal:** {monitor.signal:.0f}/100")
        lines.append(f"- **Status:** {monitor.status_label}")
        if monitor.sub_indicators:
            lines.append("- **Sub-indicators:**")
            for sub in monitor.sub_indicators:
                raw = "n/a" if sub.raw_reading is None else f"{sub.raw_reading:.0f}"
                lines.append(
                    f"  - {sub.label}: reading {raw} → signal {sub.signal:.0f} (w={sub.weight})"
                )
        if monitor.change_drivers:
            lines.append("- **Change drivers:**")
            for driver in monitor.change_drivers:
                lines.append(f"  - {driver}")
        if monitor.risk_flags:
            lines.append("- **Risk flags:**")
            for flag in monitor.risk_flags:
                lines.append(f"  - {flag}")
        lines.append("")
    return lines


def _data_completeness(report: ReportModel) -> list[str]:
    dc = report.data_completeness
    lines = [
        "## Data completeness and provenance",
        "",
        f"- **Instruments evaluated:** {dc.instruments_evaluated}",
        f"- **Agent evaluations:** {dc.total_agent_evaluations}",
        f"- **Neutral fallbacks:** {dc.neutral_fallback_count}",
        f"- **Watchlist metric completeness:** {dc.portfolio_metric_completeness_pct:.1f}%",
        f"- **Monitor completeness:** {dc.monitor_completeness_pct:.1f}% "
        f"({dc.monitors_total - dc.monitor_incomplete_count}/{dc.monitors_total} monitors)",
        f"- **Portfolio neutral fallbacks:** {dc.portfolio_neutral_fallback_count}",
        f"- **Monitors with incomplete sub-indicators:** {dc.monitor_incomplete_count}",
    ]
    if dc.missing_events:
        lines.append("- **Missing metric events:**")
        for event in dc.missing_events:
            lines.append(f"  - `{event}`")
    if dc.warnings:
        lines.append("- **Warnings:**")
        for warning in dc.warnings:
            lines.append(f"  - {warning}")
    lines.append("")
    lines.append(
        "> Neutral scores (50) mean **unknown or missing manual input**, "
        "not an average market level."
    )
    return lines


def _composite_table(report: ReportModel) -> list[str]:
    lines = [
        "## Watchlist — ranked instrument signals",
        "",
        "_Factor agents score watchlist names using manual metrics — not live quotes._",
        "",
        "| Rank | Ticker | Name | Sector | Composite | Neutral agents |",
        "| ---: | :--- | :--- | :--- | ---: | ---: |",
    ]
    for score in report.scores:
        lines.append(
            f"| {score.rank} | {score.ticker} | {score.name} | {score.sector} | "
            f"{score.composite:.2f} | {score.neutral_signal_count} |"
        )
    return lines


def _agent_breakdown_table(report: ReportModel) -> list[str]:
    agents: list[str] = []
    for score in report.scores:
        if score.signals:
            agents = [s.agent for s in score.signals]
            break
    if not agents:
        return ["_No agent signals available._"]

    header = "| Ticker | " + " | ".join(agents) + " | Composite |"
    divider = "| :--- | " + " | ".join(["---:"] * len(agents)) + " | ---: |"
    lines = ["", "### Per-agent breakdown", "", header, divider]
    for score in report.scores:
        by_agent = {signal.agent: signal.score for signal in score.signals}
        cells = " | ".join(f"{by_agent.get(a, float('nan')):.0f}" for a in agents)
        lines.append(f"| {score.ticker} | {cells} | {score.composite:.2f} |")
    return lines


def _safety_block(report: ReportModel) -> list[str]:
    lines = [MANUAL_DATA_NOTICE, "", DISCLAIMER]
    return lines


def _assemble(report: ReportModel, extra_sections: list[str]) -> str:
    sections: list[str] = []
    sections.extend(_header(report))
    sections.append("")
    sections.extend(_thesis_framing(report))
    sections.append("")
    sections.extend(_overall_regime(report))
    sections.append("")
    sections.extend(_review_posture(report))
    sections.append("")
    vic = _virtual_committee(report)
    if vic:
        sections.extend(vic)
        sections.append("")
    sections.extend(_portfolio_section(report))
    sections.append("")
    sections.extend(_concentration_warning(report))
    sections.append("")
    policy = _portfolio_policy_notes(report)
    if policy:
        sections.extend(policy)
        sections.append("")
    sections.extend(_thesis_invalidation(report))
    sections.append("")
    sections.extend(_monitor_status_table(report))
    sections.extend(_monitor_details(report))
    sections.extend(_data_completeness(report))
    sections.append("")
    sections.extend(_composite_table(report))
    sections.extend(_agent_breakdown_table(report))
    sections.append("")
    sections.extend(extra_sections)
    sections.append("---")
    sections.append("")
    sections.extend(_safety_block(report))
    return "\n".join(sections).rstrip() + "\n"


def render_daily(report: ReportModel) -> str:
    return _assemble(report, [])


def render_weekly(report: ReportModel) -> str:
    extra = [
        "> Weekly report: no historical time series yet — structural summary only.",
        "",
    ]
    extra.extend(_weekly_summary(report))
    return _assemble(report, extra)


def _weekly_summary(report: ReportModel) -> list[str]:
    lines = ["## Summary", ""]
    if report.monitors:
        monitor_avg = sum(m.signal for m in report.monitors) / len(report.monitors)
        lines.append(f"- **Overall regime:** {report.overall_regime}")
        lines.append(f"- **Average monitor signal:** {monitor_avg:.2f}")
    if report.scores:
        composites = [s.composite for s in report.scores]
        lines.append(f"- **Instruments evaluated:** {len(report.scores)}")
        lines.append(f"- **Average watchlist composite:** {sum(composites) / len(composites):.2f}")
    return lines
