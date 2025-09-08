"""
밸류 팩터 계산
BMad 협업으로 구현된 밸류 투자 핵심 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Optional, Union
import logging


def calculate_earnings_yield(
    ebit: Union[float, pd.Series],
    enterprise_value: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    수익률(Earnings Yield) 계산
    
    공식: EY = EBIT / Enterprise Value
    
    Args:
        ebit: EBIT (세전이익)
        enterprise_value: 기업가치
        
    Returns:
        수익률 (높을수록 좋음)
    """
    if isinstance(ebit, pd.Series) and isinstance(enterprise_value, pd.Series):
        # Series 처리
        result = pd.Series(index=ebit.index, dtype=float)
        valid_mask = (ebit.notna()) & (enterprise_value.notna()) & (enterprise_value != 0)
        result[valid_mask] = ebit[valid_mask] / enterprise_value[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(ebit) or pd.isna(enterprise_value) or enterprise_value == 0:
            return np.nan
        return ebit / enterprise_value


def calculate_fcf_yield(
    operating_cash_flow: Union[float, pd.Series],
    capital_expenditures: Union[float, pd.Series],
    market_cap: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    FCF 수익률(Free Cash Flow Yield) 계산
    
    공식: FCF Yield = (Operating Cash Flow - Capital Expenditures) / Market Cap
    
    Args:
        operating_cash_flow: 영업현금흐름
        capital_expenditures: 자본지출 (보통 음수)
        market_cap: 시가총액
        
    Returns:
        FCF 수익률 (높을수록 좋음)
    """
    # FCF 계산 (CapEx는 보통 음수이므로 빼기)
    fcf = operating_cash_flow - capital_expenditures
    
    if isinstance(fcf, pd.Series) and isinstance(market_cap, pd.Series):
        # Series 처리
        result = pd.Series(index=fcf.index, dtype=float)
        valid_mask = (fcf.notna()) & (market_cap.notna()) & (market_cap != 0)
        result[valid_mask] = fcf[valid_mask] / market_cap[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(fcf) or pd.isna(market_cap) or market_cap == 0:
            return np.nan
        return fcf / market_cap


def calculate_book_to_market(
    total_equity: Union[float, pd.Series],
    market_cap: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    B/M 비율(Book-to-Market) 계산
    
    공식: B/M = Total Equity / Market Cap
    
    Args:
        total_equity: 총자본
        market_cap: 시가총액
        
    Returns:
        B/M 비율 (높을수록 좋음)
    """
    if isinstance(total_equity, pd.Series) and isinstance(market_cap, pd.Series):
        # Series 처리
        result = pd.Series(index=total_equity.index, dtype=float)
        valid_mask = (total_equity.notna()) & (market_cap.notna()) & (market_cap != 0)
        result[valid_mask] = total_equity[valid_mask] / market_cap[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(total_equity) or pd.isna(market_cap) or market_cap == 0:
            return np.nan
        return total_equity / market_cap


def calculate_ev_ebit(
    enterprise_value: Union[float, pd.Series],
    ebit: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    EV/EBIT 비율 계산
    
    공식: EV/EBIT = Enterprise Value / EBIT
    
    Args:
        enterprise_value: 기업가치
        ebit: EBIT
        
    Returns:
        EV/EBIT 비율 (낮을수록 좋음)
    """
    if isinstance(enterprise_value, pd.Series) and isinstance(ebit, pd.Series):
        # Series 처리
        result = pd.Series(index=enterprise_value.index, dtype=float)
        valid_mask = (enterprise_value.notna()) & (ebit.notna()) & (ebit != 0)
        result[valid_mask] = enterprise_value[valid_mask] / ebit[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(enterprise_value) or pd.isna(ebit) or ebit == 0:
            return np.nan
        return enterprise_value / ebit


def calculate_pe_ratio(
    market_cap: Union[float, pd.Series],
    net_income: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    P/E 비율 계산
    
    공식: P/E = Market Cap / Net Income
    
    Args:
        market_cap: 시가총액
        net_income: 순이익
        
    Returns:
        P/E 비율 (낮을수록 좋음)
    """
    if isinstance(market_cap, pd.Series) and isinstance(net_income, pd.Series):
        # Series 처리
        result = pd.Series(index=market_cap.index, dtype=float)
        valid_mask = (market_cap.notna()) & (net_income.notna()) & (net_income != 0)
        result[valid_mask] = market_cap[valid_mask] / net_income[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(market_cap) or pd.isna(net_income) or net_income == 0:
            return np.nan
        return market_cap / net_income


def calculate_pb_ratio(
    market_cap: Union[float, pd.Series],
    total_equity: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    P/B 비율 계산
    
    공식: P/B = Market Cap / Total Equity
    
    Args:
        market_cap: 시가총액
        total_equity: 총자본
        
    Returns:
        P/B 비율 (낮을수록 좋음)
    """
    if isinstance(market_cap, pd.Series) and isinstance(total_equity, pd.Series):
        # Series 처리
        result = pd.Series(index=market_cap.index, dtype=float)
        valid_mask = (market_cap.notna()) & (total_equity.notna()) & (total_equity != 0)
        result[valid_mask] = market_cap[valid_mask] / total_equity[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(market_cap) or pd.isna(total_equity) or total_equity == 0:
            return np.nan
        return market_cap / total_equity


def calculate_ps_ratio(
    market_cap: Union[float, pd.Series],
    revenue: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    P/S 비율 계산
    
    공식: P/S = Market Cap / Revenue
    
    Args:
        market_cap: 시가총액
        revenue: 매출액
        
    Returns:
        P/S 비율 (낮을수록 좋음)
    """
    if isinstance(market_cap, pd.Series) and isinstance(revenue, pd.Series):
        # Series 처리
        result = pd.Series(index=market_cap.index, dtype=float)
        valid_mask = (market_cap.notna()) & (revenue.notna()) & (revenue != 0)
        result[valid_mask] = market_cap[valid_mask] / revenue[valid_mask]
        return result
    else:
        # Scalar 처리
        if pd.isna(market_cap) or pd.isna(revenue) or revenue == 0:
            return np.nan
        return market_cap / revenue
