"""Typer command-line interface for MIIP (Michael Investment Intelligence Platform)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer

from . import __version__
from .datasource import DEFAULT_SNAPSHOT_PATH, StaticDataSource
from .loaders import DEFAULT_CONFIG_DIR, ConfigError, load_app_config
from .models import AppConfig
from .pipeline import Pipeline, iso_week_label
from .reporting.render import render_daily, render_weekly

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="MIIP — manual-input investment intelligence for Michael (Slice 2).",
)
report_app = typer.Typer(no_args_is_help=True, help="Generate research reports.")
app.add_typer(report_app, name="report")

ConfigDirOption = typer.Option(DEFAULT_CONFIG_DIR, "--config-dir", help="Config directory.")
DataOption = typer.Option(DEFAULT_SNAPSHOT_PATH, "--data", help="Static data snapshot path.")
WatchlistOption = typer.Option(None, "--watchlist", "-w", help="Watchlist name.")
ModelOption = typer.Option(None, "--model", "-m", help="Scoring model name.")
DailyDateOption = typer.Option(
    None, "--date", formats=["%Y-%m-%d"], help="Report date (default: today, UTC)."
)
WeeklyDateOption = typer.Option(
    None, "--date", formats=["%Y-%m-%d"], help="A date within the target week (default: today)."
)
DailyOutOption = typer.Option(None, "--out", help="Output path (default: reports/daily/<date>.md).")
WeeklyOutOption = typer.Option(
    None, "--out", help="Output path (default: reports/weekly/<week>.md)."
)


def _load(config_dir: Path) -> AppConfig:
    try:
        return load_app_config(config_dir)
    except ConfigError as exc:
        typer.secho(f"Configuration error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _build_pipeline(config_dir: Path, data: Path) -> Pipeline:
    config = _load(config_dir)
    return Pipeline(config, StaticDataSource(data))


def _write_report(content: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


@app.command()
def version() -> None:
    """Print the MIIP version."""

    typer.echo(f"miip {__version__}")


@app.command(name="validate-config")
def validate_config(config_dir: Path = ConfigDirOption, data: Path = DataOption) -> None:
    """Validate all configuration and the data snapshot."""

    config = _load(config_dir)
    try:
        snapshot = StaticDataSource(data).snapshot()
    except ConfigError as exc:
        typer.secho(f"Data error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho("Configuration OK", fg=typer.colors.GREEN)
    typer.echo(f"  platform:        {config.platform}")
    typer.echo(
        f"  portfolio:       {config.portfolio.owner} ({len(config.portfolio.holdings)} holdings)"
    )
    typer.echo(f"  MIIP monitors:   {', '.join(sorted(config.monitors))}")
    typer.echo(f"  watchlists:      {', '.join(sorted(config.watchlists))}")
    typer.echo(f"  agents (enabled): {', '.join(n for n, c in config.agents.items() if c.enabled)}")
    typer.echo(f"  scoring models:  {', '.join(sorted(config.scoring_models))}")
    typer.echo(f"  default model:   {config.default_scoring_model}")
    typer.echo(f"  data snapshot:   {len(snapshot.metrics)} instruments, as of {snapshot.as_of}")
    if snapshot.placeholder:
        typer.secho(
            "  note: snapshot is manual/static data (not live market data)",
            fg=typer.colors.YELLOW,
        )


@app.command()
def watchlists(config_dir: Path = ConfigDirOption) -> None:
    """List configured watchlists and their instruments."""

    config = _load(config_dir)
    for name, watchlist in config.watchlists.items():
        marker = " (default)" if name == config.settings.default_watchlist else ""
        typer.secho(f"{name}{marker}", fg=typer.colors.CYAN, bold=True)
        if watchlist.description:
            typer.echo(f"  {watchlist.description}")
        for instrument in watchlist.instruments:
            typer.echo(f"  - {instrument.ticker}: {instrument.name} [{instrument.sector}]")


@app.command()
def score(
    config_dir: Path = ConfigDirOption,
    data: Path = DataOption,
    watchlist: str | None = WatchlistOption,
    model: str | None = ModelOption,
) -> None:
    """Compute and print ranked research signals to stdout."""

    pipeline = _build_pipeline(config_dir, data)
    try:
        scores = pipeline.run(watchlist, model)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    wl = pipeline.resolve_watchlist(watchlist)
    md = pipeline.resolve_scoring_model(model)
    typer.secho(f"Watchlist '{wl}' scored with model '{md}':", bold=True)
    for s in scores:
        typer.echo(f"  {s.rank:>2}. {s.ticker:<5} {s.composite:6.2f}  {s.name}")
    typer.secho(
        "These are relative research signals, not financial advice.",
        fg=typer.colors.YELLOW,
    )


def _default_out(config: AppConfig, subdir: str, filename: str, out: Path | None) -> Path:
    if out is not None:
        return out
    base = Path(config.settings.reports_dir)
    sub = config.settings.daily_subdir if subdir == "daily" else config.settings.weekly_subdir
    return base / sub / filename


@report_app.command("daily")
def report_daily(
    config_dir: Path = ConfigDirOption,
    data: Path = DataOption,
    watchlist: str | None = WatchlistOption,
    model: str | None = ModelOption,
    report_date: datetime = DailyDateOption,
    out: Path = DailyOutOption,
) -> None:
    """Generate a daily research report."""

    pipeline = _build_pipeline(config_dir, data)
    day = report_date.date() if report_date else datetime.now(UTC).date()
    generated_at = datetime.now(UTC)
    try:
        report = pipeline.build_report(
            report_type="daily",
            period_label=day.isoformat(),
            title=f"Daily Research Signals - {day.isoformat()}",
            watchlist_name=watchlist,
            scoring_model_name=model,
            generated_at=generated_at,
        )
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    out_path = _default_out(pipeline.config, "daily", f"{day.isoformat()}.md", out)
    _write_report(render_daily(report), out_path)
    typer.secho(f"Wrote daily report to {out_path}", fg=typer.colors.GREEN)


@report_app.command("weekly")
def report_weekly(
    config_dir: Path = ConfigDirOption,
    data: Path = DataOption,
    watchlist: str | None = WatchlistOption,
    model: str | None = ModelOption,
    report_date: datetime = WeeklyDateOption,
    out: Path = WeeklyOutOption,
) -> None:
    """Generate a weekly research report."""

    pipeline = _build_pipeline(config_dir, data)
    day = report_date.date() if report_date else datetime.now(UTC).date()
    week = iso_week_label(day)
    generated_at = datetime.now(UTC)
    try:
        report = pipeline.build_report(
            report_type="weekly",
            period_label=week,
            title=f"Weekly Research Signals - {week}",
            watchlist_name=watchlist,
            scoring_model_name=model,
            generated_at=generated_at,
        )
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    out_path = _default_out(pipeline.config, "weekly", f"{week}.md", out)
    _write_report(render_weekly(report), out_path)
    typer.secho(f"Wrote weekly report to {out_path}", fg=typer.colors.GREEN)


if __name__ == "__main__":  # pragma: no cover
    app()
