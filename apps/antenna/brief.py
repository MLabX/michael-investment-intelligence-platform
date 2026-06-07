"""Render a Brief to the Morning Discovery Brief markdown format."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import Brief

SYDNEY = ZoneInfo("Australia/Sydney")

DISCLAIMER = (
    "_Not investment advice. No stock recommendations. This brief surfaces things that may be "
    "worth attention across AI, Robotics, Space, China, and Macro — nothing more._"
)


def render(
    brief: Brief,
    *,
    date: datetime,
    candidate_count: int,
    dedup_skipped: int = 0,
) -> str:
    sydney = date.astimezone(SYDNEY) if date.tzinfo else date.replace(tzinfo=SYDNEY)
    date_str = sydney.strftime("%Y-%m-%d")
    lines = [
        "# Morning Discovery Brief",
        "",
        f"**Date:** {date_str} (Australia/Sydney)  ",
        "**Themes:** AI · Robotics · Space · China · Macro  ",
        f"**Scanned:** {candidate_count} candidate items  ",
    ]
    if dedup_skipped:
        lines.append(f"**Cross-day dedup:** {dedup_skipped} repeat items skipped  ")
    lines += [
        f"**Analyzer:** {brief.analyzer}",
        "",
        DISCLAIMER,
        "",
        "## Top Signals Today",
        "",
    ]

    if brief.is_empty:
        lines += [
            "**Nothing Important Today.**",
            "",
            "No meaningful signal cleared the bar across the tracked themes. "
            "A quiet day is a valid result — attention is the scarce resource.",
            "",
        ]
    else:
        for i, sig in enumerate(brief.signals, start=1):
            title = f"[{sig.title}]({sig.link})" if sig.link else sig.title
            themes = ", ".join(t.upper() for t in sig.related_themes)
            lines += [
                f"### {i}. {title}",
                "",
                f"- **Source:** {sig.source}",
                f"- **Summary:** {sig.summary}",
                f"- **Why it matters:** {sig.why_it_matters}",
                f"- **Related themes:** {themes}",
                f"- **Confidence:** {sig.confidence}",
                "",
            ]

    lines += [
        "---",
        f"_Generated {sydney.strftime('%Y-%m-%d %H:%M %Z')} by Antenna MVP._",
        "",
    ]
    return "\n".join(lines)


def write_brief(
    brief: Brief,
    *,
    out_dir: Path,
    candidate_count: int,
    date: datetime | None = None,
    dedup_skipped: int = 0,
) -> Path:
    date = date or datetime.now(SYDNEY)
    sydney = date.astimezone(SYDNEY) if date.tzinfo else date.replace(tzinfo=SYDNEY)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sydney.strftime('%Y-%m-%d')}.md"
    path.write_text(
        render(brief, date=sydney, candidate_count=candidate_count, dedup_skipped=dedup_skipped),
        encoding="utf-8",
    )
    return path
