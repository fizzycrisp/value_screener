#!/usr/bin/env python3
"""
KOSPI 200 종목 밸류 스크리너
FinanceDataReader를 사용하여 KOSPI 200 종목을 가져오고 밸류 스크리닝을 수행합니다.
"""
import sys
import os
import pandas as pd
from typing import List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import FinanceDataReader as fdr
except ImportError:
    print("FinanceDataReader가 설치되지 않았습니다. 'pip install finance-datareader'를 실행하세요.")
    sys.exit(1)

from value_screener.cli import main as screener_main
from value_screener.config import load_config

def get_kospi200_tickers() -> List[str]:
    """KOSPI 상위 200 종목 리스트를 가져옵니다."""
    try:
        print("KOSPI 종목 리스트를 가져오는 중...")
        kospi = fdr.StockListing('KOSPI')
        
        # 시가총액으로 정렬하여 상위 200개 선택
        kospi_sorted = kospi.sort_values('Marcap', ascending=False)
        kospi200 = kospi_sorted.head(200)
        
        # 종목 코드에 .KS 접미사 추가
        tickers = [f"{code}.KS" for code in kospi200['Code'].tolist()]
        
        print(f"총 {len(tickers)}개 종목을 찾았습니다.")
        print("상위 10개 종목:")
        for i, ticker in enumerate(tickers[:10]):
            name = kospi200.iloc[i]['Name']
            marcap = kospi200.iloc[i]['Marcap']
            print(f"  {ticker} - {name} (시총: {marcap:,.0f}원)")
        
        return tickers
    
    except Exception as e:
        print(f"KOSPI 종목 리스트를 가져오는 중 오류 발생: {e}")
        return []

def run_kospi_screening(tickers: List[str], output_file: str = "reports/kospi200_results.csv", 
                       report_file: str = "reports/kospi200_report.md", max_workers: int = 4, timeout: float = 15.0):
    """KOSPI 200 종목에 대해 밸류 스크리닝을 실행합니다."""
    
    if not tickers:
        print("검사할 종목이 없습니다.")
        return
    
    print(f"\n{len(tickers)}개 종목에 대해 밸류 스크리닝을 시작합니다...")
    print(f"병렬 처리: {max_workers}개 워커, 타임아웃: {timeout}초")
    
    # CLI 인수 설정
    sys.argv = [
        'kospi_screener.py',
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

def main():
    """메인 함수"""
    print("=== KOSPI 200 밸류 스크리너 ===")
    
    # KOSPI 200 종목 리스트 가져오기
    tickers = get_kospi200_tickers()
    
    if not tickers:
        print("종목 리스트를 가져올 수 없습니다.")
        return
    
    # 사용자에게 실행 여부 확인
    response = input(f"\n{len(tickers)}개 종목을 검사하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("검사를 취소했습니다.")
        return
    
    # 스크리닝 실행
    run_kospi_screening(tickers)

if __name__ == '__main__':
    main()
