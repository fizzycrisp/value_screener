"""
CLI 진입점
BMad 협업으로 구현된 저평가 주식 스크리닝 시스템의 명령행 인터페이스
"""
import click
import yaml
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
from datetime import date, datetime

from .data import YFinanceConnector, CSVConnector
from .schemas import validate_data_schema
from .factors import FactorCalculator


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              default='configs/default.yaml', help='설정 파일 경로')
@click.option('--verbose', '-v', is_flag=True, help='상세 로그 출력')
@click.pass_context
def cli(ctx, config, verbose):
    """저평가 주식 스크리닝 알고리즘 CLI"""
    # 설정 로드
    with open(config, 'r', encoding='utf-8') as f:
        ctx.obj['config'] = yaml.safe_load(f)
    
    # 로깅 설정
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ctx.ensure_object(dict)


@cli.command()
@click.option('--source', type=click.Choice(['yfinance', 'csv']), 
              default='yfinance', help='데이터 소스')
@click.option('--tickers', help='분석할 종목 코드들 (쉼표로 구분)')
@click.option('--file', type=click.Path(exists=True), help='CSV 파일 경로 (source=csv일 때)')
@click.option('--output', '-o', type=click.Path(), help='결과 출력 파일 경로')
@click.option('--md', is_flag=True, help='마크다운 형식으로 출력')
@click.pass_context
def screen(ctx, source, tickers, file, output, md):
    """주식 스크리닝 실행"""
    config = ctx.obj['config']
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting screening with source: {source}")
    
    # 데이터 커넥터 설정
    if source == 'yfinance':
        if not tickers:
            raise click.UsageError("--tickers is required when source=yfinance")
        
        connector = YFinanceConnector(config.get('data_sources', {}).get('yfinance', {}))
        tickers_list = [t.strip() for t in tickers.split(',')]
        
    elif source == 'csv':
        if not file:
            raise click.UsageError("--file is required when source=csv")
        
        connector = CSVConnector({
            'file_path': file,
            **config.get('data_sources', {}).get('csv', {})
        })
        tickers_list = [t.strip() for t in tickers.split(',')] if tickers else None
        
    else:
        raise click.UsageError(f"Unsupported source: {source}")
    
    try:
        # 데이터 가져오기
        logger.info("Fetching universe data...")
        universe_df = connector.fetch_universe(tickers_list, date.today())
        
        if universe_df.empty:
            logger.warning("No universe data retrieved")
            return
        
        # 스키마 검증
        universe_df = validate_data_schema(universe_df, 'universe')
        
        # 재무 데이터 가져오기
        logger.info("Fetching fundamentals data...")
        fundamentals_df = connector.fetch_fundamentals(tickers_list, date.today())
        
        if not fundamentals_df.empty:
            fundamentals_df = validate_data_schema(fundamentals_df, 'fundamentals')
        
        # 데이터 병합
        df = pd.merge(universe_df, fundamentals_df, on='ticker', how='left', suffixes=('', '_fund'))
        
        # 팩터 계산
        logger.info("Calculating factors...")
        factor_calc = FactorCalculator(config)
        factors_df = factor_calc.calculate_all_factors(df)
        
        # 결과 출력
        if md:
            display_results_markdown(factors_df)
        else:
            display_results_table(factors_df)
        
        # 파일 저장
        if output:
            save_results(factors_df, output)
            logger.info(f"Results saved to {output}")
        
        logger.info("Screening completed successfully")
        
    except Exception as e:
        logger.error(f"Screening failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--source', type=click.Choice(['yfinance', 'csv']), 
              default='yfinance', help='데이터 소스')
@click.option('--tickers', multiple=True, help='백테스트할 종목 코드들')
@click.option('--file', type=click.Path(exists=True), help='CSV 파일 경로 (source=csv일 때)')
@click.option('--start', type=click.DateTime(formats=['%Y-%m-%d']), 
              default='2018-01-01', help='백테스트 시작일')
@click.option('--end', type=click.DateTime(formats=['%Y-%m-%d']), 
              default='2025-08-31', help='백테스트 종료일')
@click.option('--output', '-o', type=click.Path(), help='결과 출력 디렉토리')
@click.pass_context
def backtest(ctx, source, tickers, file, start, end, output):
    """백테스트 실행"""
    config = ctx.obj['config']
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting backtest from {start.date()} to {end.date()}")
    
    # TODO: 백테스트 엔진 구현
    click.echo("Backtest functionality will be implemented in the next phase")
    logger.info("Backtest completed (placeholder)")


@cli.command()
@click.option('--source', type=click.Choice(['yfinance', 'csv']), 
              default='yfinance', help='데이터 소스')
@click.option('--tickers', multiple=True, help='분석할 종목 코드들')
@click.option('--file', type=click.Path(exists=True), help='CSV 파일 경로 (source=csv일 때)')
@click.pass_context
def validate(ctx, source, tickers, file):
    """데이터 스키마 검증"""
    config = ctx.obj['config']
    logger = logging.getLogger(__name__)
    
    logger.info("Validating data schema...")
    
    # 데이터 커넥터 설정
    if source == 'yfinance':
        if not tickers:
            raise click.UsageError("--tickers is required when source=yfinance")
        
        connector = YFinanceConnector(config.get('data_sources', {}).get('yfinance', {}))
        tickers_list = [t.strip() for t in tickers.split(',')]
        
    elif source == 'csv':
        if not file:
            raise click.UsageError("--file is required when source=csv")
        
        connector = CSVConnector({
            'file_path': file,
            **config.get('data_sources', {}).get('csv', {})
        })
        tickers_list = [t.strip() for t in tickers.split(',')] if tickers else None
        
    else:
        raise click.UsageError(f"Unsupported source: {source}")
    
    try:
        # 데이터 가져오기 및 검증
        universe_df = connector.fetch_universe(tickers_list, date.today())
        
        if universe_df.empty:
            logger.warning("No data to validate")
            return
        
        # 스키마 검증
        validated_df = validate_data_schema(universe_df, 'universe')
        
        # 검증 결과 출력
        click.echo(f"✅ Schema validation passed for {len(validated_df)} records")
        click.echo(f"📊 Columns: {len(validated_df.columns)}")
        click.echo(f"📈 Sample data:")
        click.echo(validated_df.head().to_string())
        
        logger.info("Schema validation completed successfully")
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise click.ClickException(str(e))


def display_results_markdown(df: pd.DataFrame):
    """결과를 마크다운 형식으로 출력"""
    if df.empty:
        click.echo("No results to display")
        return
    
    # 주요 컬럼 선택
    display_columns = ['ticker', 'earnings_yield', 'fcf_yield', 'book_to_market', 
                      'gross_profitability', 'roic', 'composite_score']
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        display_df = df[available_columns].round(4)
        click.echo("\n## 스크리닝 결과")
        click.echo(display_df.to_markdown(index=False))
    else:
        click.echo(df.to_markdown(index=False))


def display_results_table(df: pd.DataFrame):
    """결과를 테이블 형식으로 출력"""
    if df.empty:
        click.echo("No results to display")
        return
    
    # 주요 컬럼 선택
    display_columns = ['ticker', 'earnings_yield', 'fcf_yield', 'book_to_market', 
                      'gross_profitability', 'roic', 'composite_score']
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        display_df = df[available_columns].round(4)
        click.echo("\n스크리닝 결과:")
        click.echo(display_df.to_string(index=False))
    else:
        click.echo(df.to_string(index=False))


def save_results(df: pd.DataFrame, output_path: str):
    """결과를 파일로 저장"""
    output_path = Path(output_path)
    
    if output_path.suffix.lower() == '.csv':
        df.to_csv(output_path, index=False)
    elif output_path.suffix.lower() == '.xlsx':
        df.to_excel(output_path, index=False)
    else:
        # 기본적으로 CSV로 저장
        df.to_csv(f"{output_path}.csv", index=False)


def main():
    """메인 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()
