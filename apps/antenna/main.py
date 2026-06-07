"""Antenna MVP entry point: fetch -> dedupe -> analyze -> write a daily discovery brief.

Run (from repo root):
    PYTHONPATH=apps python -m antenna
    PYTHONPATH=apps python -m antenna --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import analyze
from .brief import write_brief
from .config import load_config
from .fetch import fetch_all
from .seen import DEFAULT_SEEN_PATH, filter_items, load_seen, record_signals, save_seen

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = REPO_ROOT / "reports" / "discovery" / "daily"
SYDNEY = ZoneInfo("Australia/Sydney")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Antenna MVP — daily discovery brief.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory.")
    parser.add_argument(
        "--seen", type=Path, default=DEFAULT_SEEN_PATH, help="Cross-day dedup JSON store."
    )
    parser.add_argument("--hours", type=int, default=None, help="Override lookback window (hours).")
    parser.add_argument("--feeds", type=Path, default=None, help="Override feeds.yaml path.")
    parser.add_argument(
        "--no-dedup", action="store_true", help="Disable cross-day deduplication (debug only)."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.feeds)
    if args.hours:
        config = config.__class__(**{**config.__dict__, "lookback_hours": args.hours})

    now_utc = datetime.now(UTC)
    now_sydney = now_utc.astimezone(SYDNEY)
    brief_date = now_sydney.strftime("%Y-%m-%d")

    raw_items = fetch_all(config, now=now_utc)
    seen = load_seen(args.seen)
    if args.no_dedup:
        items, skipped = raw_items, 0
    else:
        items, skipped = filter_items(raw_items, seen)

    brief = analyze(items, config)
    path = write_brief(
        brief,
        out_dir=args.out,
        candidate_count=len(raw_items),
        date=now_sydney,
        dedup_skipped=skipped,
    )

    if not args.no_dedup and brief.signals:
        save_seen(args.seen, record_signals(brief.signals, seen, date=brief_date))

    status = "Nothing Important Today" if brief.is_empty else f"{len(brief.signals)} signals"
    print(
        f"Wrote {path} — {status} "
        f"(analyzer: {brief.analyzer}, {len(raw_items)} fetched, {skipped} deduped)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
