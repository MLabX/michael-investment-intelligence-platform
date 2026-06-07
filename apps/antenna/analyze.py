"""Turn candidate items into a small set of ranked signals.

Two analyzers, chosen automatically:
  * LLM analyzer (default when OPENAI_API_KEY is set): selects + writes the brief.
  * Heuristic analyzer (offline fallback): keyword + recency scoring, so the MVP
    is runnable and testable with no API key and produces real output from real data.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .config import Config
from .fetch import Item

log = logging.getLogger("antenna.analyze")

# Keywords used by the heuristic analyzer for relevance + cross-theme tagging.
THEME_KEYWORDS = {
    "ai": [
        "ai",
        "model",
        "llm",
        "gpt",
        "openai",
        "anthropic",
        "deepmind",
        "neural",
        "inference",
        "training",
        "gpu",
        "chip",
        "nvidia",
        "datacenter",
        "data center",
        "agent",
    ],
    "robotics": [
        "robot",
        "humanoid",
        "automation",
        "actuator",
        "manipulation",
        "autonomous",
        "drone",
        "warehouse",
        "boston dynamics",
        "tesla bot",
    ],
    "space": [
        "space",
        "rocket",
        "launch",
        "satellite",
        "orbit",
        "spacex",
        "starship",
        "nasa",
        "lunar",
        "moon",
        "mars",
        "payload",
    ],
    "china": [
        "china",
        "chinese",
        "beijing",
        "yuan",
        "renminbi",
        "pboc",
        "xi ",
        "shanghai",
        "shenzhen",
        "hong kong",
        "huawei",
        "byd",
    ],
    "macro": [
        "fed",
        "inflation",
        "rate",
        "rates",
        "yield",
        "treasury",
        "gdp",
        "recession",
        "jobs",
        "cpi",
        "central bank",
        "ecb",
        "imf",
        "monetary",
    ],
}


@dataclass
class Signal:
    source: str
    title: str
    link: str
    summary: str
    why_it_matters: str
    related_themes: list[str]
    confidence: str  # Low | Medium | High


@dataclass
class Brief:
    signals: list[Signal] = field(default_factory=list)
    nothing_important: bool = False
    analyzer: str = "heuristic"

    @property
    def is_empty(self) -> bool:
        return self.nothing_important or not self.signals


# --------------------------------------------------------------------------- #
# Heuristic analyzer (no API key needed)
# --------------------------------------------------------------------------- #
def _related_themes(text: str, primary: str) -> list[str]:
    low = text.lower()
    themes = [primary]
    for theme, words in THEME_KEYWORDS.items():
        if theme == primary:
            continue
        if any(w in low for w in words):
            themes.append(theme)
    return themes


def _score(item: Item, now: datetime) -> int:
    text = f"{item.title} {item.summary}".lower()
    score = sum(text.count(w) for w in THEME_KEYWORDS.get(item.theme, []))
    # Recency bonus: anything in the last 12h gets a nudge.
    if item.published and (now - item.published).total_seconds() < 12 * 3600:
        score += 2
    return score


def analyze_heuristic(items: list[Item], config: Config) -> Brief:
    if not items:
        return Brief(nothing_important=True, analyzer="heuristic")

    now = datetime.now(UTC)
    ranked = sorted(items, key=lambda i: _score(i, now), reverse=True)

    # Light diversity: cap items per source so one prolific feed can't dominate.
    per_source: dict[str, int] = {}
    chosen: list[Item] = []
    for item in ranked:
        if per_source.get(item.source, 0) >= 2:
            continue
        per_source[item.source] = per_source.get(item.source, 0) + 1
        chosen.append(item)
        if len(chosen) >= config.max_signals:
            break

    signals: list[Signal] = []
    for item in chosen:
        score = _score(item, now)
        confidence = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
        summary = item.summary or item.title
        signals.append(
            Signal(
                source=item.source,
                title=item.title,
                link=item.link,
                summary=summary[:300],
                why_it_matters=(
                    f"Surfaced under the {item.theme.upper()} theme as potentially worth "
                    "attention. (Heuristic mode — no LLM judgement applied.)"
                ),
                related_themes=_related_themes(f"{item.title} {item.summary}", item.theme),
                confidence=confidence,
            )
        )
    return Brief(signals=signals, analyzer="heuristic")


# --------------------------------------------------------------------------- #
# LLM analyzer (OpenAI)
# --------------------------------------------------------------------------- #
_SYSTEM = (
    "You are a discovery analyst for a busy long-term investor and technology leader. "
    "You scan news across five themes: AI, Robotics, Space, China, Macro. "
    "Your ONLY job is to identify what genuinely deserves attention today. "
    "You do NOT give investment advice and you do NOT recommend buying or selling anything. "
    "Be ruthless: most days have little that matters. Prefer structural, early, or surprising "
    "developments over routine news, press cycles, and echoes of the same story. "
    "If nothing meaningful happened, say so."
)


def _build_prompt(items: list[Item], config: Config) -> str:
    lines = [
        f"Select at most {config.max_signals} items that truly deserve attention today.",
        "Skip routine, duplicated, or low-substance items. A quiet day is fine.",
        "",
        "Return STRICT JSON:",
        '{ "nothing_important": bool,',
        '  "signals": [ { "index": int, "summary": str, "why_it_matters": str,',
        '                 "related_themes": [str], "confidence": "Low|Medium|High" } ] }',
        "- summary: one neutral sentence on what happened.",
        "- why_it_matters: one sentence on why it could matter to long-term themes (no advice).",
        "- related_themes: any of ai, robotics, space, china, macro.",
        "- confidence: how confident you are this is genuinely important.",
        "",
        "CANDIDATES:",
    ]
    for idx, item in enumerate(items):
        when = item.published.strftime("%Y-%m-%d") if item.published else "undated"
        lines.append(
            f"[{idx}] ({item.theme}) {when} | {item.source} | {item.title} :: {item.summary[:240]}"
        )
    return "\n".join(lines)


def analyze_llm(items: list[Item], config: Config) -> Brief:
    if not items:
        return Brief(nothing_important=True, analyzer="llm")

    from openai import OpenAI  # imported lazily so the package works without the dep

    client = OpenAI()
    resp = client.chat.completions.create(
        model=config.model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _build_prompt(items, config)},
        ],
    )
    data = json.loads(resp.choices[0].message.content or "{}")
    return parse_llm_response(data, items, config)


def parse_llm_response(data: dict, items: list[Item], config: Config) -> Brief:
    """Map LLM JSON output to a Brief. Separated for unit testing."""
    if data.get("nothing_important"):
        return Brief(nothing_important=True, analyzer="llm")

    signals: list[Signal] = []
    for raw in data.get("signals", [])[: config.max_signals]:
        if not isinstance(raw, dict):
            continue
        try:
            item = items[int(raw["index"])]
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        related = [t for t in raw.get("related_themes", []) if isinstance(t, str)] or [item.theme]
        signals.append(
            Signal(
                source=item.source,
                title=item.title,
                link=item.link,
                summary=str(raw.get("summary", item.title))[:400],
                why_it_matters=str(raw.get("why_it_matters", "")).strip()[:400],
                related_themes=related,
                confidence=str(raw.get("confidence", "Medium")).capitalize(),
            )
        )
    if not signals:
        return Brief(nothing_important=True, analyzer="llm")
    return Brief(signals=signals, analyzer="llm")


def analyze(items: list[Item], config: Config) -> Brief:
    """Use the LLM analyzer when a key is available; otherwise the heuristic fallback."""
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return analyze_llm(items, config)
        except Exception as exc:  # fall back rather than fail the daily run
            log.warning("LLM analyzer failed (%s); using heuristic fallback", exc)
    else:
        log.info("OPENAI_API_KEY not set; using heuristic analyzer")
    return analyze_heuristic(items, config)
