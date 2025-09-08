"""
리스크 팩터 계산
BMad 협업으로 구현된 리스크 관련 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Union


def calculate_beneish_m_score(
    dsri: Union[float, pd.Series],
    gmi: Union[float, pd.Series],
    aqi: Union[float, pd.Series],
    sgi: Union[float, pd.Series],
    depi: Union[float, pd.Series],
    sgai: Union[float, pd.Series],
    lvgi: Union[float, pd.Series],
    tata: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    Beneish M-Score 계산
    
    공식: M-Score = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 
                    0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    
    Args:
        dsri: Days Sales in Receivables Index
        gmi: Gross Margin Index
        aqi: Asset Quality Index
        sgi: Sales Growth Index
        depi: Depreciation Index
        sgai: Sales General and Administrative expenses Index
        lvgi: Leverage Index
        tata: Total Accruals to Total Assets
        
    Returns:
        Beneish M-Score (낮을수록 좋음, -2.22 이하가 안전)
    """
    m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 
               0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
    
    return m_score


def calculate_altman_z_score(
    working_capital: Union[float, pd.Series],
    retained_earnings: Union[float, pd.Series],
    ebit: Union[float, pd.Series],
    market_value_equity: Union[float, pd.Series],
    sales: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    Altman Z-Score 계산
    
    공식: Z-Score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
    where:
    A = Working Capital / Total Assets
    B = Retained Earnings / Total Assets
    C = EBIT / Total Assets
    D = Market Value Equity / Total Liabilities
    E = Sales / Total Assets
    
    Args:
        working_capital: 운전자본
        retained_earnings: 이익잉여금
        ebit: EBIT
        market_value_equity: 시장가치 자본
        sales: 매출액
        total_assets: 총자산
        
    Returns:
        Altman Z-Score (높을수록 좋음, 2.99 이상이 안전)
    """
    # A: Working Capital / Total Assets
    a = working_capital / total_assets
    
    # B: Retained Earnings / Total Assets
    b = retained_earnings / total_assets
    
    # C: EBIT / Total Assets
    c = ebit / total_assets
    
    # D: Market Value Equity / Total Liabilities (간단한 근사)
    # Total Liabilities ≈ Total Assets - Total Equity
    total_liabilities = total_assets - (market_value_equity / 2)  # 간단한 근사
    d = market_value_equity / total_liabilities
    
    # E: Sales / Total Assets
    e = sales / total_assets
    
    z_score = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
    
    return z_score


def calculate_volatility(
    returns: Union[float, pd.Series],
    window: int = 252
) -> Union[float, pd.Series]:
    """
    변동성 계산
    
    Args:
        returns: 수익률 시리즈
        window: 계산 윈도우 (기본값: 252일)
        
    Returns:
        변동성 (낮을수록 좋음)
    """
    if isinstance(returns, pd.Series):
        return returns.rolling(window=window).std() * np.sqrt(252)  # 연환산
    else:
        return np.nan


def calculate_beta(
    stock_returns: Union[float, pd.Series],
    market_returns: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    베타 계산
    
    Args:
        stock_returns: 주식 수익률
        market_returns: 시장 수익률
        
    Returns:
        베타 (1에 가까울수록 시장과 동조)
    """
    if isinstance(stock_returns, pd.Series) and isinstance(market_returns, pd.Series):
        # 공분산과 시장 분산 계산
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        
        if market_variance != 0:
            return covariance / market_variance
        else:
            return np.nan
    else:
        return np.nan


def calculate_max_drawdown(
    cumulative_returns: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    최대 낙폭 계산
    
    Args:
        cumulative_returns: 누적 수익률
        
    Returns:
        최대 낙폭 (낮을수록 좋음)
    """
    if isinstance(cumulative_returns, pd.Series):
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()
    else:
        return np.nan
