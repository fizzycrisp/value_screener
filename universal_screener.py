#!/usr/bin/env python3
"""
범용 주식 스크리너
KOSPI, NASDAQ 등 다양한 시장의 주식을 분석할 수 있습니다.
"""
import sys
import os
import pandas as pd
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import FinanceDataReader as fdr
except ImportError:
    print("FinanceDataReader가 설치되지 않았습니다. 'pip install finance-datareader'를 실행하세요.")
    sys.exit(1)

from value_screener.cli import main as screener_main
from value_screener.config import load_config

# 지원하는 시장 정의
SUPPORTED_MARKETS = {
    'kospi': {
        'name': 'KOSPI',
        'description': '한국 종합주가지수',
        'suffix': '.KS',
        'sort_by': 'Marcap',
        'top_n': 200
    },
    'kosdaq': {
        'name': 'KOSDAQ',
        'description': '코스닥 시장',
        'suffix': '.KQ',
        'sort_by': 'Marcap',
        'top_n': 200
    },
    'nasdaq': {
        'name': 'NASDAQ',
        'description': '나스닥 종합지수',
        'suffix': '',
        'sort_by': None,  # NASDAQ에는 시가총액 컬럼이 없음
        'top_n': 500
    }
}

def get_market_tickers(market: str, top_n: int = None) -> List[str]:
    """지정된 시장의 상위 종목 리스트를 가져옵니다."""
    
    if market not in SUPPORTED_MARKETS:
        raise ValueError(f"지원하지 않는 시장입니다: {market}. 지원 시장: {list(SUPPORTED_MARKETS.keys())}")
    
    market_info = SUPPORTED_MARKETS[market]
    top_n = top_n or market_info['top_n']
    
    try:
        print(f"{market_info['name']} 종목 리스트를 가져오는 중...")
        stocks = fdr.StockListing(market_info['name'])
        
        # 시가총액으로 정렬하여 상위 N개 선택
        if market_info['sort_by'] and market_info['sort_by'] in stocks.columns:
            stocks_sorted = stocks.sort_values(market_info['sort_by'], ascending=False)
            top_stocks = stocks_sorted.head(top_n)
        else:
            # 시가총액 컬럼이 없으면 처음 N개 사용
            top_stocks = stocks.head(top_n)
        
        # 종목 코드에 접미사 추가
        tickers = []
        for _, row in top_stocks.iterrows():
            if market in ('kospi', 'kosdaq'):
                ticker = f"{row['Code']}{market_info['suffix']}"
            else:  # nasdaq
                ticker = f"{row['Symbol']}{market_info['suffix']}"
            tickers.append(ticker)
        
        print(f"총 {len(tickers)}개 종목을 찾았습니다.")
        print("상위 10개 종목:")
        for i, ticker in enumerate(tickers[:10]):
            if market == 'kospi':
                name = top_stocks.iloc[i]['Name']
                marcap = top_stocks.iloc[i].get('Marcap', 'N/A')
                print(f"  {ticker} - {name} (시총: {marcap})")
            else:  # nasdaq
                name = top_stocks.iloc[i]['Name']
                print(f"  {ticker} - {name}")
        
        return tickers
    
    except Exception as e:
        print(f"{market_info['name']} 종목 리스트를 가져오는 중 오류 발생: {e}")
        return []

def run_market_screening(market: str, top_n: int = None, 
                        output_file: str = None, report_file: str = None,
                        max_workers: int = 4, timeout: float = 15.0):
    """지정된 시장의 종목에 대해 밸류 스크리닝을 실행합니다."""
    
    market_info = SUPPORTED_MARKETS[market]
    top_n = top_n or market_info['top_n']
    
    # 기본 파일명 설정
    if output_file is None:
        output_file = f"reports/{market}_top{top_n}_results.csv"
    if report_file is None:
        report_file = f"reports/{market}_top{top_n}_report.md"
    
    # 종목 리스트 가져오기
    tickers = get_market_tickers(market, top_n)
    
    if not tickers:
        print("검사할 종목이 없습니다.")
        return
    
    print(f"\n{len(tickers)}개 종목에 대해 밸류 스크리닝을 시작합니다...")
    print(f"병렬 처리: {max_workers}개 워커, 타임아웃: {timeout}초")
    
    # CLI 인수 설정
    sys.argv = [
        'universal_screener.py',
        '--source', 'yfinance',
        '--output', output_file,
        '--report', report_file,
        '--md',
        '--max-workers', str(max_workers),
        '--timeout', str(timeout),
        '--quiet'
    ]
    
    # 각 종목을 --tickers 옵션으로 추가
    for ticker in tickers:
        sys.argv.extend(['--tickers', ticker])
    
    try:
        # 밸류 스크리너 실행
        screener_main()
        print(f"\n결과가 {output_file}에 저장되었습니다.")
        print(f"분석 리포트가 {report_file}에 저장되었습니다.")
        
    except Exception as e:
        print(f"스크리닝 중 오류 발생: {e}")

def list_supported_markets():
    """지원하는 시장 목록을 출력합니다."""
    print("=== 지원하는 시장 ===")
    for key, info in SUPPORTED_MARKETS.items():
        print(f"{key}: {info['name']} - {info['description']}")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='범용 주식 밸류 스크리너')
    parser.add_argument('market', nargs='?', choices=list(SUPPORTED_MARKETS.keys()) + ['list'],
                       help='분석할 시장 (list: 지원 시장 목록)')
    parser.add_argument('--tickers', nargs='*', help='직접 지정할 티커 목록 (지정 시 market/top 무시)')
    parser.add_argument('--yes', '-y', action='store_true', help='프롬프트 없이 바로 실행')
    parser.add_argument('--top', type=int, help='상위 N개 종목 (기본값: 시장별 기본값)')
    parser.add_argument('--output', help='CSV 출력 파일 경로')
    parser.add_argument('--report', help='리포트 출력 파일 경로')
    parser.add_argument('--workers', type=int, default=4, help='병렬 처리 워커 수 (기본값: 4)')
    parser.add_argument('--timeout', type=float, default=15.0, help='종목당 타임아웃 (초) (기본값: 15)')
    
    args = parser.parse_args()
    
    if args.market == 'list' and not args.tickers:
        list_supported_markets()
        return
    
    # 티커 직접 지정 모드
    if args.tickers:
        print(f"직접 지정된 {len(args.tickers)}개 티커에 대해 스크리닝을 실행합니다...")
        # value_screener CLI를 직접 호출
        sys.argv = [
            'universal_screener.py',
            '--source','yfinance',
            '--md',
            '--max-workers', str(args.workers),
            '--timeout', str(args.timeout)
        ]
        if args.output:
            sys.argv += ['--output', args.output]
        if args.report:
            sys.argv += ['--report', args.report]
        for tk in args.tickers:
            sys.argv += ['--tickers', tk]
        screener_main()
        return

    print(f"=== {SUPPORTED_MARKETS[args.market]['name']} 밸류 스크리너 ===")

    # 사용자에게 실행 여부 확인 (스킵 옵션 지원)
    top_n = args.top or SUPPORTED_MARKETS[args.market]['top_n']
    if not args.yes:
        response = input(f"\n{top_n}개 종목을 검사하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("검사를 취소했습니다.")
            return

    # 스크리닝 실행
    run_market_screening(
        market=args.market,
        top_n=args.top,
        output_file=args.output,
        report_file=args.report,
        max_workers=args.workers,
        timeout=args.timeout
    )

if __name__ == '__main__':
    main()
