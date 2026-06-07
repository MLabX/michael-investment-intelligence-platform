"""Cross-day deduplication via a simple JSON file.

Tracks items already surfaced in prior briefs. An item reappears only when its
content hash changes (material update). No database, no cloud dependency.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .fetch import Item

log = logging.getLogger("antenna.seen")

DEFAULT_SEEN_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "antenna" / "seen.json"


@dataclass
class SeenRecord:
    content_hash: str
    title: str
    last_seen: str  # ISO date YYYY-MM-DD


def item_key(item: Item) -> str:
    if item.link:
        return item.link.strip().lower()
    return item.title.strip().lower()


def content_hash(item: Item) -> str:
    payload = f"{item.title}\n{item.summary}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def load_seen(path: Path) -> dict[str, SeenRecord]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("could not load seen store (%s); starting fresh", exc)
        return {}

    out: dict[str, SeenRecord] = {}
    for key, rec in (raw.get("items") or {}).items():
        if isinstance(rec, dict) and "content_hash" in rec:
            out[str(key)] = SeenRecord(
                content_hash=str(rec["content_hash"]),
                title=str(rec.get("title", "")),
                last_seen=str(rec.get("last_seen", "")),
            )
    return out


def save_seen(path: Path, seen: dict[str, SeenRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "items": {
            key: {
                "content_hash": rec.content_hash,
                "title": rec.title,
                "last_seen": rec.last_seen,
            }
            for key, rec in seen.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_repeat(item: Item, seen: dict[str, SeenRecord]) -> bool:
    key = item_key(item)
    prior = seen.get(key)
    if prior is None:
        return False
    return prior.content_hash == content_hash(item)


def filter_items(items: list[Item], seen: dict[str, SeenRecord]) -> tuple[list[Item], int]:
    """Drop items already surfaced with unchanged content. Returns (kept, skipped_count)."""
    kept: list[Item] = []
    skipped = 0
    for item in items:
        if is_repeat(item, seen):
            skipped += 1
            continue
        kept.append(item)
    return kept, skipped


def record_signals(
    signals: list, seen: dict[str, SeenRecord], *, date: str
) -> dict[str, SeenRecord]:
    """Merge surfaced brief signals into the seen store."""
    updated = dict(seen)
    for sig in signals:
        key = sig.link.strip().lower() if sig.link else sig.title.strip().lower()
        payload = f"{sig.title}\n{sig.summary}".encode()
        updated[key] = SeenRecord(
            content_hash=hashlib.sha256(payload).hexdigest()[:16],
            title=sig.title,
            last_seen=date,
        )
    return updated
