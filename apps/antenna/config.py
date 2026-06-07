"""Load feeds.yaml. Nothing clever."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import THEMES

FEEDS_PATH = Path(__file__).parent / "feeds.yaml"


@dataclass(frozen=True)
class Feed:
    theme: str
    name: str
    url: str


@dataclass(frozen=True)
class Config:
    feeds: list[Feed]
    lookback_hours: int = 30
    max_signals: int = 8
    max_candidates: int = 120
    feed_timeout_seconds: int = 15
    model: str = "gpt-4o-mini"
    extra: dict = field(default_factory=dict)


def load_config(path: Path | None = None) -> Config:
    path = path or FEEDS_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = raw.get("settings", {}) or {}

    feeds: list[Feed] = []
    for item in raw.get("feeds", []) or []:
        theme = str(item.get("theme", "")).lower().strip()
        if theme not in THEMES:
            raise ValueError(f"Feed {item!r} has unknown theme {theme!r}; allowed: {THEMES}")
        feeds.append(Feed(theme=theme, name=str(item["name"]), url=str(item["url"])))

    if not feeds:
        raise ValueError(f"No feeds defined in {path}")

    return Config(
        feeds=feeds,
        lookback_hours=int(settings.get("lookback_hours", 30)),
        max_signals=int(settings.get("max_signals", 8)),
        max_candidates=int(settings.get("max_candidates", 120)),
        feed_timeout_seconds=int(settings.get("feed_timeout_seconds", 15)),
        # env var wins so CI can override without editing YAML.
        model=os.environ.get("ANTENNA_MODEL") or str(settings.get("model", "gpt-4o-mini")),
    )
