"""Fetch and normalise items from public RSS/Atom feeds.

Resilient by design: a broken/changed/blocked/timed-out feed is logged and
skipped, never fatal. The brief should still generate from whatever feeds responded.
"""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import feedparser

from .config import Config, Feed

log = logging.getLogger("antenna.fetch")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_USER_AGENT = "Antenna-MVP/0.1 (+https://github.com/MLabX/michael-investment-intelligence-platform)"


@dataclass
class Item:
    theme: str
    source: str
    title: str
    link: str
    summary: str
    published: datetime | None  # tz-aware UTC, or None if the feed omitted it


def _clean(text: str, limit: int = 500) -> str:
    text = _TAG_RE.sub(" ", text or "")
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def _published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            try:
                return datetime(*value[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                continue
    return None


def fetch_feed_bytes(url: str, *, timeout: int) -> bytes:
    """Fetch raw feed bytes with a hard per-feed timeout."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed(feed: Feed, content: bytes, *, cutoff: datetime) -> list[Item]:
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(str(parsed.get("bozo_exception", "invalid feed")))

    items: list[Item] = []
    for entry in parsed.entries:
        published = _published(entry)
        if published is not None and published < cutoff:
            continue
        title = _clean(entry.get("title", ""), limit=300)
        if not title:
            continue
        items.append(
            Item(
                theme=feed.theme,
                source=feed.name,
                title=title,
                link=entry.get("link", ""),
                summary=_clean(entry.get("summary", entry.get("description", ""))),
                published=published,
            )
        )
    return items


def fetch_feed(feed: Feed, *, cutoff: datetime, timeout: int) -> list[Item]:
    try:
        content = fetch_feed_bytes(feed.url, timeout=timeout)
    except TimeoutError:
        log.warning("feed timeout: %s (%s)", feed.name, feed.url)
        return []
    except urllib.error.URLError as exc:
        log.warning("feed fetch failed: %s (%s) — %s", feed.name, feed.url, exc)
        return []

    try:
        items = parse_feed(feed, content, cutoff=cutoff)
    except Exception as exc:
        log.warning("feed parse failed: %s (%s) — %s", feed.name, feed.url, exc)
        return []

    log.info("feed ok: %s — %d items in window", feed.name, len(items))
    return items


def _dedupe(items: list[Item]) -> list[Item]:
    seen: set[str] = set()
    out: list[Item] = []
    for item in items:
        key = (item.link or item.title).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def fetch_all(config: Config, *, now: datetime | None = None) -> list[Item]:
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(hours=config.lookback_hours)

    items: list[Item] = []
    for feed in config.feeds:
        try:
            items.extend(fetch_feed(feed, cutoff=cutoff, timeout=config.feed_timeout_seconds))
        except Exception as exc:  # never let one feed kill the run
            log.warning("feed error: %s (%s) — %s", feed.name, feed.url, exc)

    items = _dedupe(items)
    items.sort(key=lambda i: i.published or datetime.min.replace(tzinfo=UTC), reverse=True)
    if len(items) > config.max_candidates:
        items = items[: config.max_candidates]
    log.info("fetched %d candidate items from %d feeds", len(items), len(config.feeds))
    return items
