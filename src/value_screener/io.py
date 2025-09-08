from typing import List, Optional
import pandas as pd
from tabulate import tabulate
from pathlib import Path
from datetime import datetime
import numpy as np

REQUIRED_COLUMNS = [
    "ticker","price","shares_outstanding","total_debt","cash_and_equivalents",
    "ebit","ebitda","operating_cash_flow","capital_expenditures"
]

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "ticker" not in df.columns:
        raise ValueError("CSV must include a 'ticker' column.")
    return df

def format_market_cap(value) -> str:
    """시가총액을 읽기 쉬운 단위로 포맷팅합니다."""
    if pd.isna(value) or value is None:
        return "N/A"
    
    # 이미 문자열로 포맷팅된 경우 그대로 반환
    if isinstance(value, str):
        return value
    
    try:
        value = float(value)
        if value >= 1e12:  # 1조 이상
            return f"{value/1e12:.1f}조"
        elif value >= 1e8:  # 1억 이상
            return f"{value/1e8:.1f}억"
        elif value >= 1e4:  # 1만 이상
            return f"{value/1e4:.1f}만"
        else:
            return f"{value:,.0f}"
    except (ValueError, TypeError):
        return str(value)

def format_enterprise_value(value) -> str:
    """기업가치를 읽기 쉬운 단위로 포맷팅합니다."""
    if pd.isna(value) or value is None:
        return "N/A"
    
    # 이미 문자열로 포맷팅된 경우 그대로 반환
    if isinstance(value, str):
        return value
    
    try:
        value = float(value)
        if value >= 1e12:  # 1조 이상
            return f"{value/1e12:.1f}조"
        elif value >= 1e8:  # 1억 이상
            return f"{value/1e8:.1f}억"
        elif value >= 1e4:  # 1만 이상
            return f"{value/1e4:.1f}만"
        else:
            return f"{value:,.0f}"
    except (ValueError, TypeError):
        return str(value)

def df_to_markdown(df: pd.DataFrame) -> str:
    # 시가총액과 기업가치 포맷팅
    df_formatted = df.copy()
    
    if 'market_cap' in df_formatted.columns:
        df_formatted['market_cap'] = df_formatted['market_cap'].apply(format_market_cap)
    
    if 'enterprise_value' in df_formatted.columns:
        df_formatted['enterprise_value'] = df_formatted['enterprise_value'].apply(format_enterprise_value)
    
    return tabulate(df_formatted, headers="keys", tablefmt="github", showindex=False)

def save_csv(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def generate_analysis_report(df: pd.DataFrame, output_path: str = "reports/screening_report.md") -> None:
    """스크리닝 결과를 분석하여 마크다운 리포트를 생성합니다."""
    
    # 리포트 내용 생성
    report_content = _create_report_content(df)
    
    # 파일 저장
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"분석 리포트가 {output_path}에 저장되었습니다.")

def _create_report_content(df: pd.DataFrame) -> str:
    """리포트 내용을 생성합니다."""
    
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    # 기본 통계
    total_stocks = len(df)
    passed_stocks = df['passed_filters'].sum() if 'passed_filters' in df.columns else 0
    
    # EV/EBIT 통계
    ev_ebit_valid = df[df['ev_ebit'].notna()] if 'ev_ebit' in df.columns else pd.DataFrame()
    ev_ebit_count = len(ev_ebit_valid)
    ev_ebit_range_count = 0
    ev_ebit_range_stocks = pd.DataFrame()
    
    if ev_ebit_count > 0:
        ev_ebit_range_stocks = ev_ebit_valid[(ev_ebit_valid['ev_ebit'] >= 5) & (ev_ebit_valid['ev_ebit'] <= 12)]
        ev_ebit_range_count = len(ev_ebit_range_stocks)
    
    # 데이터 누락 현황
    fcf_count = df['fcf_yield'].notna().sum() if 'fcf_yield' in df.columns else 0
    roic_count = df['roic'].notna().sum() if 'roic' in df.columns else 0
    net_debt_count = df['net_debt_ebitda'].notna().sum() if 'net_debt_ebitda' in df.columns else 0
    
    # 리포트 내용 생성
    content = f"""# 밸류 스크리닝 분석 리포트

**생성일시**: {current_time}

## 📊 전체 요약

- **총 분석 종목 수**: {total_stocks:,}개
- **필터 통과 종목**: {passed_stocks}개
- **통과율**: {(passed_stocks/total_stocks*100):.1f}%

## 📈 지표별 분석

### EV/EBIT (기업가치/영업이익)
- **계산 가능한 종목**: {ev_ebit_count}개 ({(ev_ebit_count/total_stocks*100):.1f}%)
- **5-12 범위 종목**: {ev_ebit_range_count}개

"""
    
    if ev_ebit_count > 0:
        content += f"""- **평균**: {ev_ebit_valid['ev_ebit'].mean():.2f}
- **중간값**: {ev_ebit_valid['ev_ebit'].median():.2f}
- **최소값**: {ev_ebit_valid['ev_ebit'].min():.2f}
- **최대값**: {ev_ebit_valid['ev_ebit'].max():.2f}

"""
    
    content += f"""### 기타 지표
- **FCF 수익률 계산 가능**: {fcf_count}개
- **ROIC 계산 가능**: {roic_count}개
- **순부채/EBITDA 계산 가능**: {net_debt_count}개

## 🏆 필터 통과 종목

"""
    
    if passed_stocks > 0:
        passed_df = df[df['passed_filters'] == True]
        content += f"총 {passed_stocks}개 종목이 모든 필터를 통과했습니다:\n\n"
        content += df_to_markdown(passed_df[['ticker', 'name', 'ev_ebit', 'fcf_yield', 'roic', 'net_debt_ebitda']])
        content += "\n\n"
    else:
        content += "모든 종목이 필터를 통과하지 못했습니다.\n\n"
    
    # EV/EBIT 5-12 범위 종목
    if ev_ebit_range_count > 0:
        content += f"""## 💎 EV/EBIT 5-12 범위 종목 ({ev_ebit_range_count}개)

합리적인 밸류에이션 범위에 있는 종목들입니다:

"""
        content += df_to_markdown(ev_ebit_range_stocks[['ticker', 'name', 'ev_ebit']])
        content += "\n\n"
    
    # 상위 10개 종목 (시가총액 기준)
    if 'market_cap' in df.columns:
        top_market_cap = df.nlargest(10, 'market_cap')
        content += """## 🏢 시가총액 상위 10개 종목

"""
        # 시가총액 포맷팅을 위해 복사본 생성
        top_market_cap_formatted = top_market_cap[['ticker', 'name', 'market_cap', 'ev_ebit']].copy()
        top_market_cap_formatted['market_cap'] = top_market_cap_formatted['market_cap'].apply(format_market_cap)
        content += df_to_markdown(top_market_cap_formatted)
        content += "\n\n"
    
    # 결론 및 권고사항
    content += """## 📝 결론 및 권고사항

### 주요 발견사항
"""
    
    if passed_stocks == 0:
        content += "- 현재 시장 상황에서 완전한 밸류 필터를 통과하는 종목이 없습니다.\n"
    
    if ev_ebit_range_count > 0:
        content += f"- EV/EBIT 5-12 범위에 {ev_ebit_range_count}개 종목이 있어 상대적으로 합리적인 밸류에이션을 보입니다.\n"
    
    if fcf_count == 0 and roic_count == 0:
        content += "- Yahoo Finance 데이터 제한으로 FCF 수익률과 ROIC 계산이 어렵습니다.\n"
    
    content += """
### 투자 시 고려사항
- 이 분석은 교육 목적으로만 사용하세요
- 실제 투자 전 추가적인 재무 분석이 필요합니다
- 시장 상황과 개별 기업의 사업 전망을 종합적으로 고려하세요
- 분산투자와 리스크 관리가 중요합니다

---
*본 리포트는 자동으로 생성되었으며, 투자 조언이 아닙니다.*
"""
    
    return content
