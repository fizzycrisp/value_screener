import sys
import concurrent.futures as cf
from typing import List, Optional
import click
import pandas as pd
from tqdm import tqdm

from .config import load_config
from .io import df_to_markdown, load_csv, save_csv, generate_analysis_report
from .fetchers import fetch_yfinance, from_csv_row, FinancialRow
from .screening import build_rows, apply_filters
from .business.screening.strategy_factory import StrategyFactory

@click.command()
@click.option("--source", type=click.Choice(["yfinance","csv"]), required=True, help="Data source.")
@click.option("--tickers", multiple=True, help="Tickers (space-separated). Example: AAPL MSFT")
@click.option("--file", "file_path", type=click.Path(exists=True, dir_okay=False), help="CSV when --source=csv.")
@click.option("--config", "config_path", type=click.Path(exists=True, dir_okay=False), help="YAML thresholds config.")
@click.option("--strategy", type=click.Choice(["value","growth","quality","buffett"]), default="value", show_default=True,
              help="Screening strategy to apply.")
@click.option("--no-filter", is_flag=True, help="Do not filter; only compute metrics.")
@click.option("--output", type=click.Path(), help="Optional CSV output path.")
@click.option("--md", is_flag=True, help="Print markdown table.")
@click.option("--report", type=click.Path(), help="Generate analysis report (markdown file).")
@click.option("--timeout", type=float, default=10.0, help="Per-ticker timeout (yfinance).")
@click.option("--max-workers", type=int, default=8, help="Parallel fetch workers.")
@click.option("-q","--quiet", is_flag=True, help="Reduce logs.")
def main(source, tickers, file_path, config_path, strategy, no_filter, output, md, report, timeout, max_workers, quiet):
    cfg = load_config(config_path)

    if source == "csv":
        if not file_path:
            raise click.UsageError("--file is required when --source=csv")
        raw = load_csv(file_path)
        fin_rows: List[FinancialRow] = [from_csv_row(r) for _, r in raw.iterrows()]
    elif source == "yfinance":
        tickers = list(tickers)
        if not tickers:
            raise click.UsageError("--tickers is required when --source=yfinance")
        fin_rows = fetch_yfinance(tickers, timeout=timeout, max_workers=max_workers)
    else:
        raise click.UsageError("Unsupported --source")

    df = build_rows(fin_rows)
    if not no_filter:
        # 우선 기존 기본 필터(value 기본값)를 유지하면서, 선택된 전략이 있으면 전략을 적용
        try:
            strat = StrategyFactory.create_strategy(strategy)
            df = strat.apply(df, cfg)
        except Exception as e:
            if not quiet:
                click.echo(f"전략 적용 오류: {e}. 기본 필터를 사용합니다.")
            df = apply_filters(df, cfg)

    # Pretty print
    show_cols = ["ticker","name","price","market_cap","enterprise_value","ev_ebit","fcf_yield","roic","net_debt_ebitda"]
    show_cols = [c for c in show_cols if c in df.columns]
    out_df = df[show_cols + (["passed_filters"] if "passed_filters" in df.columns else [])].copy()

    # Format a bit
    for c in ["price","market_cap","enterprise_value"]:
        if c in out_df.columns:
            out_df[c] = out_df[c].map(lambda x: None if pd.isna(x) else float(x))
    for c in ["ev_ebit","fcf_yield","roic","net_debt_ebitda"]:
        if c in out_df.columns:
            out_df[c] = out_df[c].map(lambda x: None if pd.isna(x) else float(x))

    if md:
        print(df_to_markdown(out_df))
    else:
        # Plain text
        with pd.option_context("display.max_columns", None, "display.width", 160):
            print(out_df.to_string(index=False))

    if output:
        save_csv(out_df, output)
        if not quiet:
            click.echo(f"Saved CSV to: {output}")
    
    if report:
        generate_analysis_report(out_df, report)
