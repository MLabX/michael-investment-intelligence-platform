"""Antenna MVP behaviour tests — focused, not exhaustive."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from antenna.analyze import Brief, Signal, analyze_heuristic, parse_llm_response
from antenna.brief import render, write_brief
from antenna.config import Config, Feed, load_config
from antenna.fetch import Item, fetch_all, fetch_feed, fetch_feed_bytes, parse_feed
from antenna.main import main
from antenna.seen import (
    SeenRecord,
    content_hash,
    filter_items,
    is_repeat,
    item_key,
    load_seen,
    record_signals,
    save_seen,
)


def _item(
    *,
    theme: str = "ai",
    title: str = "Test headline",
    link: str = "https://example.com/a",
    summary: str = "Summary text",
) -> Item:
    return Item(
        theme=theme,
        source="Test Source",
        title=title,
        link=link,
        summary=summary,
        published=datetime(2026, 6, 7, 8, 0, tzinfo=UTC),
    )


def _config(feeds: list[Feed] | None = None) -> Config:
    return Config(
        feeds=feeds or [Feed(theme="ai", name="Test", url="https://example.com/feed.xml")],
        lookback_hours=30,
        max_signals=3,
        max_candidates=10,
        feed_timeout_seconds=5,
    )


# --- cross-day dedup ------------------------------------------------------- #
class TestSeen:
    def test_seen_item_is_filtered(self):
        item = _item()
        seen = {
            item_key(item): SeenRecord(
                content_hash=content_hash(item), title=item.title, last_seen="2026-06-06"
            )
        }
        kept, skipped = filter_items([item], seen)
        assert kept == []
        assert skipped == 1

    def test_new_item_is_accepted(self):
        item = _item(title="Brand new story")
        kept, skipped = filter_items([item], {})
        assert len(kept) == 1
        assert skipped == 0

    def test_material_update_is_accepted(self):
        item = _item(summary="Updated summary with new facts")
        seen = {
            item_key(item): SeenRecord(
                content_hash="oldhash00000000", title=item.title, last_seen="2026-06-06"
            )
        }
        assert not is_repeat(item, seen)
        kept, skipped = filter_items([item], seen)
        assert len(kept) == 1
        assert skipped == 0

    def test_persistence_roundtrip(self, tmp_path: Path):
        path = tmp_path / "seen.json"
        item = _item()
        seen = record_signals(
            [Signal("src", item.title, item.link, item.summary, "why", ["ai"], "High")],
            {},
            date="2026-06-07",
        )
        save_seen(path, seen)
        loaded = load_seen(path)
        assert item_key(item) in loaded
        assert loaded[item_key(item)].last_seen == "2026-06-07"


# --- empty report ---------------------------------------------------------- #
class TestEmptyReport:
    def test_nothing_important_render(self):
        text = render(
            Brief(nothing_important=True, analyzer="llm"),
            date=datetime(2026, 6, 7, 6, 30, tzinfo=UTC),
            candidate_count=0,
        )
        assert "# Morning Discovery Brief" in text
        assert "**Nothing Important Today.**" in text
        assert "Australia/Sydney" in text

    def test_heuristic_empty_when_no_items(self):
        brief = analyze_heuristic([], _config())
        assert brief.is_empty


# --- feed resilience ------------------------------------------------------- #
class TestFeedResilience:
    def test_broken_feed_does_not_fail_run(self):
        good = Feed(theme="ai", name="Good", url="https://good.example/feed")
        bad = Feed(theme="macro", name="Bad", url="https://bad.example/feed")
        config = _config(feeds=[good, bad])

        with patch("antenna.fetch.fetch_feed") as mock_fetch:
            mock_fetch.side_effect = [
                [_item(title="Good story")],
                RuntimeError("boom"),
            ]
            items = fetch_all(config)
        assert len(items) == 1
        assert items[0].title == "Good story"

    def test_parse_feed_invalid_content(self):
        feed = Feed(theme="ai", name="Bad XML", url="https://example.com/x")
        with pytest.raises(ValueError):
            parse_feed(feed, b"not xml at all", cutoff=datetime(2020, 1, 1, tzinfo=UTC))


# --- timeout handling ------------------------------------------------------ #
class TestTimeout:
    def test_timeout_returns_empty_list(self):
        feed = Feed(theme="ai", name="Slow", url="https://slow.example/feed")
        with patch("antenna.fetch.fetch_feed_bytes", side_effect=TimeoutError("timed out")):
            items = fetch_feed(feed, cutoff=datetime(2020, 1, 1, tzinfo=UTC), timeout=1)
        assert items == []

    def test_fetch_bytes_uses_timeout(self):
        with patch("antenna.fetch.urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"<rss/>"
            fetch_feed_bytes("https://example.com/feed", timeout=7)
            mock_open.assert_called_once()
            assert mock_open.call_args.kwargs["timeout"] == 7


# --- report rendering ------------------------------------------------------ #
class TestReportRendering:
    def test_markdown_structure(self):
        brief = Brief(
            signals=[
                Signal(
                    source="SpaceNews",
                    title="Launch happened",
                    link="https://example.com/launch",
                    summary="A rocket launched.",
                    why_it_matters="Signals demand for launch capacity.",
                    related_themes=["space"],
                    confidence="High",
                )
            ],
            analyzer="llm",
        )
        text = render(
            brief,
            date=datetime(2026, 6, 7, 20, 0, tzinfo=UTC),
            candidate_count=42,
            dedup_skipped=3,
        )
        assert "## Top Signals Today" in text
        assert "### 1." in text
        assert "- **Source:** SpaceNews" in text
        assert "- **Why it matters:**" in text
        assert "**Cross-day dedup:** 3 repeat items skipped" in text

    def test_write_brief_creates_file(self, tmp_path: Path):
        brief = Brief(nothing_important=True, analyzer="heuristic")
        path = write_brief(
            brief, out_dir=tmp_path, candidate_count=0, date=datetime(2026, 6, 7, tzinfo=UTC)
        )
        assert path.exists()
        assert path.name == "2026-06-07.md"


# --- LLM response mapping -------------------------------------------------- #
class TestLlmMapping:
    def test_valid_response(self):
        items = [_item(title="Alpha"), _item(title="Beta", link="https://example.com/b")]
        data = {
            "nothing_important": False,
            "signals": [
                {
                    "index": 0,
                    "summary": "Alpha happened.",
                    "why_it_matters": "Could shift AI capex.",
                    "related_themes": ["ai", "macro"],
                    "confidence": "High",
                }
            ],
        }
        brief = parse_llm_response(data, items, _config())
        assert not brief.is_empty
        assert brief.signals[0].title == "Alpha"
        assert brief.analyzer == "llm"

    def test_malformed_response(self):
        items = [_item()]
        data = {
            "nothing_important": False,
            "signals": [{"index": "bad"}, {"index": 99}, "not-a-dict"],
        }
        brief = parse_llm_response(data, items, _config())
        assert brief.is_empty


# --- CLI smoke test -------------------------------------------------------- #
class TestCli:
    def test_end_to_end_minimal(self, tmp_path: Path):
        out = tmp_path / "reports"
        seen = tmp_path / "seen.json"
        item = _item()

        with (
            patch("antenna.main.fetch_all", return_value=[item]),
            patch("antenna.main.analyze") as mock_analyze,
        ):
            mock_analyze.return_value = Brief(
                signals=[
                    Signal(
                        source=item.source,
                        title=item.title,
                        link=item.link,
                        summary=item.summary,
                        why_it_matters="Test.",
                        related_themes=["ai"],
                        confidence="Medium",
                    )
                ],
                analyzer="heuristic",
            )
            rc = main(["--out", str(out), "--seen", str(seen), "--no-dedup"])
        assert rc == 0
        assert list(out.glob("*.md"))


# --- config ---------------------------------------------------------------- #
class TestConfig:
    def test_load_feeds_yaml(self):
        config = load_config()
        assert len(config.feeds) >= 10
        assert config.feed_timeout_seconds == 15
