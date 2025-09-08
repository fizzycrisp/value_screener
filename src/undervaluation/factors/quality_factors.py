"""
퀄리티 팩터 계산
BMad 협업으로 구현된 기업 품질 핵심 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Optional, Union
import logging


def calculate_gross_profitability(
    gross_profit: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    매출총이익률(Gross Profitability) 계산
    
    공식: Gross Profitability = Gross Profit / Total Assets
    
    Args:
        gross_profit: 매출총이익
        total_assets: 총자산
        
    Returns:
        매출총이익률 (높을수록 좋음)
    """
    if isinstance(gross_profit, pd.Series) and isinstance(total_assets, pd.Series):
        # Series 처리
        result = pd.Series(index=gross_profit.index, dtype=float)
        valid_mask = (gross_profit.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = gross_profit[valid_mask] / total_assets[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(gross_profit) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return gross_profit / total_assets


def calculate_roic(
    ebit: Union[float, pd.Series],
    tax_expense: Union[float, pd.Series],
    pretax_income: Union[float, pd.Series],
    total_debt: Union[float, pd.Series],
    total_equity: Union[float, pd.Series],
    cash: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    ROIC(Return on Invested Capital) 계산 (근사치)
    
    공식:
    Tax Rate ≈ clip(Tax / Pretax, 0, 0.45) (fallback 25%)
    NOPAT = EBIT × (1 - Tax Rate)
    Invested Capital ≈ Total Debt + Total Equity - Cash
    ROIC = NOPAT / Invested Capital
    
    Args:
        ebit: EBIT
        tax_expense: 법인세비용
        pretax_income: 세전이익
        total_debt: 총부채
        total_equity: 총자본
        cash: 현금및현금성자산
        
    Returns:
        ROIC (높을수록 좋음)
    """
    # 세율 추정
    if isinstance(tax_expense, pd.Series) and isinstance(pretax_income, pd.Series):
        tax_rate = pd.Series(0.25, index=tax_expense.index)  # 기본값 25%
        valid_mask = (tax_expense.notna()) & (pretax_income.notna()) & (pretax_income != 0)
        if valid_mask.any():
            calculated_rate = tax_expense[valid_mask] / pretax_income[valid_mask]
            # 0-45% 범위로 제한
            calculated_rate = calculated_rate.clip(0, 0.45)
            tax_rate[valid_mask] = calculated_rate
    else:
        # Scalar 처리
        if pd.notna(tax_expense) and pd.notna(pretax_income) and pretax_income != 0:
            tax_rate = max(0, min(0.45, tax_expense / pretax_income))
        else:
            tax_rate = 0.25
    
    # NOPAT 계산
    nopat = ebit * (1 - tax_rate)
    
    # 투자자본 계산
    invested_capital = total_debt + total_equity - cash
    
    # ROIC 계산
    if isinstance(nopat, pd.Series) and isinstance(invested_capital, pd.Series):
        result = pd.Series(index=nopat.index, dtype=float)
        valid_mask = (nopat.notna()) & (invested_capital.notna()) & (invested_capital > 0)
        result[valid_mask] = nopat[valid_mask] / invested_capital[valid_mask]
        return result
    else:
        if pd.isna(nopat) or pd.isna(invested_capital) or invested_capital <= 0:
            return np.nan
        return nopat / invested_capital


def calculate_roe(
    net_income: Union[float, pd.Series],
    total_equity: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    ROE(Return on Equity) 계산
    
    공식: ROE = Net Income / Total Equity
    
    Args:
        net_income: 순이익
        total_equity: 총자본
        
    Returns:
        ROE (높을수록 좋음)
    """
    if isinstance(net_income, pd.Series) and isinstance(total_equity, pd.Series):
        result = pd.Series(index=net_income.index, dtype=float)
        valid_mask = (net_income.notna()) & (total_equity.notna()) & (total_equity != 0)
        result[valid_mask] = net_income[valid_mask] / total_equity[valid_mask]
        return result
    else:
        if pd.isna(net_income) or pd.isna(total_equity) or total_equity == 0:
            return np.nan
        return net_income / total_equity


def calculate_roa(
    net_income: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    ROA(Return on Assets) 계산
    
    공식: ROA = Net Income / Total Assets
    
    Args:
        net_income: 순이익
        total_assets: 총자산
        
    Returns:
        ROA (높을수록 좋음)
    """
    if isinstance(net_income, pd.Series) and isinstance(total_assets, pd.Series):
        result = pd.Series(index=net_income.index, dtype=float)
        valid_mask = (net_income.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = net_income[valid_mask] / total_assets[valid_mask]
        return result
    else:
        if pd.isna(net_income) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return net_income / total_assets


def calculate_interest_coverage(
    ebit: Union[float, pd.Series],
    interest_expense: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    이자보상배수(Interest Coverage Ratio) 계산
    
    공식: Interest Coverage = EBIT / |Interest Expense|
    
    Args:
        ebit: EBIT
        interest_expense: 이자비용
        
    Returns:
        이자보상배수 (높을수록 좋음)
    """
    # 이자비용의 절댓값 사용
    abs_interest = np.abs(interest_expense)
    
    if isinstance(ebit, pd.Series) and isinstance(abs_interest, pd.Series):
        result = pd.Series(index=ebit.index, dtype=float)
        valid_mask = (ebit.notna()) & (abs_interest.notna()) & (abs_interest != 0)
        result[valid_mask] = ebit[valid_mask] / abs_interest[valid_mask]
        return result
    else:
        if pd.isna(ebit) or pd.isna(abs_interest) or abs_interest == 0:
            return np.nan
        return ebit / abs_interest


def calculate_debt_to_equity(
    total_debt: Union[float, pd.Series],
    total_equity: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    부채비율(Debt-to-Equity) 계산
    
    공식: D/E = Total Debt / Total Equity
    
    Args:
        total_debt: 총부채
        total_equity: 총자본
        
    Returns:
        부채비율 (낮을수록 좋음)
    """
    if isinstance(total_debt, pd.Series) and isinstance(total_equity, pd.Series):
        result = pd.Series(index=total_debt.index, dtype=float)
        valid_mask = (total_debt.notna()) & (total_equity.notna()) & (total_equity != 0)
        result[valid_mask] = total_debt[valid_mask] / total_equity[valid_mask]
        return result
    else:
        if pd.isna(total_debt) or pd.isna(total_equity) or total_equity == 0:
            return np.nan
        return total_debt / total_equity


def calculate_f_score(
    roa: Union[float, pd.Series],
    cfo: Union[float, pd.Series],
    total_assets: Union[float, pd.Series],
    delta_roa: Union[float, pd.Series],
    accruals: Union[float, pd.Series],
    delta_leverage: Union[float, pd.Series],
    delta_liquidity: Union[float, pd.Series],
    equity_offered: Union[float, pd.Series],
    delta_margin: Union[float, pd.Series],
    delta_turnover: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    F-Score (Piotroski F-Score) 계산
    
    Args:
        roa: ROA
        cfo: 영업현금흐름
        total_assets: 총자산
        delta_roa: ROA 변화
        accruals: 발생액
        delta_leverage: 레버리지 변화
        delta_liquidity: 유동성 변화
        equity_offered: 신주발행
        delta_margin: 마진 변화
        delta_turnover: 회전율 변화
        
    Returns:
        F-Score (0-9, 높을수록 좋음)
    """
    # 각 지표별 점수 계산 (1점 또는 0점)
    score = 0
    
    # 1. ROA > 0
    if isinstance(roa, pd.Series):
        score = pd.Series(0, index=roa.index)
        score[roa > 0] = 1
    else:
        score = 1 if roa > 0 else 0
    
    # 2. CFO > 0
    if isinstance(cfo, pd.Series):
        cfo_score = pd.Series(0, index=cfo.index)
        cfo_score[cfo > 0] = 1
        score += cfo_score
    else:
        score += 1 if cfo > 0 else 0
    
    # 3. ROA 증가
    if isinstance(delta_roa, pd.Series):
        roa_score = pd.Series(0, index=delta_roa.index)
        roa_score[delta_roa > 0] = 1
        score += roa_score
    else:
        score += 1 if delta_roa > 0 else 0
    
    # 4. 발생액 < CFO
    if isinstance(accruals, pd.Series) and isinstance(cfo, pd.Series):
        accruals_score = pd.Series(0, index=accruals.index)
        accruals_score[accruals < cfo] = 1
        score += accruals_score
    else:
        score += 1 if accruals < cfo else 0
    
    # 5. 레버리지 감소
    if isinstance(delta_leverage, pd.Series):
        leverage_score = pd.Series(0, index=delta_leverage.index)
        leverage_score[delta_leverage < 0] = 1
        score += leverage_score
    else:
        score += 1 if delta_leverage < 0 else 0
    
    # 6. 유동성 증가
    if isinstance(delta_liquidity, pd.Series):
        liquidity_score = pd.Series(0, index=delta_liquidity.index)
        liquidity_score[delta_liquidity > 0] = 1
        score += liquidity_score
    else:
        score += 1 if delta_liquidity > 0 else 0
    
    # 7. 신주발행 없음
    if isinstance(equity_offered, pd.Series):
        equity_score = pd.Series(0, index=equity_offered.index)
        equity_score[equity_offered <= 0] = 1
        score += equity_score
    else:
        score += 1 if equity_offered <= 0 else 0
    
    # 8. 마진 증가
    if isinstance(delta_margin, pd.Series):
        margin_score = pd.Series(0, index=delta_margin.index)
        margin_score[delta_margin > 0] = 1
        score += margin_score
    else:
        score += 1 if delta_margin > 0 else 0
    
    # 9. 회전율 증가
    if isinstance(delta_turnover, pd.Series):
        turnover_score = pd.Series(0, index=delta_turnover.index)
        turnover_score[delta_turnover > 0] = 1
        score += turnover_score
    else:
        score += 1 if delta_turnover > 0 else 0
    
    return score
