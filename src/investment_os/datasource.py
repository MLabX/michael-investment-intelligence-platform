"""Data source abstraction.

Slice 2 ships ``StaticDataSource`` for manual/static YAML snapshots. The
``DataSource`` protocol is the seam for future ingestion (files, APIs) without
changing agents, scoring, or reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml
from pydantic import ValidationError

from .loaders import ConfigError
from .models import InstrumentMetrics, MarketSnapshot

DEFAULT_SNAPSHOT_PATH = Path("data") / "market_snapshot.yaml"


@runtime_checkable
class DataSource(Protocol):
    """Anything that can supply a :class:`MarketSnapshot` of metrics."""

    @property
    def label(self) -> str:
        """Human-readable identifier for use in report provenance."""

    @property
    def is_placeholder(self) -> bool:
        """True when the data is illustrative rather than real market data."""

    def snapshot(self) -> MarketSnapshot:
        """Return the current snapshot of per-instrument metrics."""


class StaticDataSource:
    """A :class:`DataSource` backed by a static YAML snapshot on disk."""

    def __init__(self, path: Path | str = DEFAULT_SNAPSHOT_PATH) -> None:
        self._path = Path(path)
        self._cached: MarketSnapshot | None = None

    @property
    def label(self) -> str:
        return f"manual/static snapshot ({self._path.name})"

    @property
    def is_placeholder(self) -> bool:
        return self.snapshot().placeholder

    def snapshot(self) -> MarketSnapshot:
        if self._cached is None:
            self._cached = self._load()
        return self._cached

    def metrics_for(self, ticker: str) -> InstrumentMetrics:
        """Return metrics for a ticker, or an empty (all-None) set if absent."""

        return self.snapshot().metrics.get(ticker, InstrumentMetrics())

    def _load(self) -> MarketSnapshot:
        if not self._path.exists():
            raise ConfigError(f"Missing data snapshot: {self._path}")
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                raw = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {self._path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError(f"Expected a mapping at the top level of {self._path}")
        try:
            return MarketSnapshot.model_validate(raw)
        except ValidationError as exc:
            raise ConfigError(f"Data snapshot validation failed:\n{exc}") from exc
