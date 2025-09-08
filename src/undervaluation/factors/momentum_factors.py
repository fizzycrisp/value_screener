"""
모멘텀 팩터 계산
BMad 협업으로 구현된 모멘텀 관련 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Union


def calculate_momentum_12m_1m(
    returns_12m: Union[float, pd.Series],
    returns_1m: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    12-1 모멘텀 계산
    
    공식: Momentum 12-1 = 12개월 수익률 - 1개월 수익률
    
    Args:
        returns_12m: 12개월 수익률
        returns_1m: 1개월 수익률
        
    Returns:
        12-1 모멘텀 (높을수록 좋음)
    """
    if isinstance(returns_12m, pd.Series) and isinstance(returns_1m, pd.Series):
        result = pd.Series(index=returns_12m.index, dtype=float)
        valid_mask = (returns_12m.notna()) & (returns_1m.notna())
        result[valid_mask] = returns_12m[valid_mask] - returns_1m[valid_mask]
        return result
    else:
        if pd.isna(returns_12m) or pd.isna(returns_1m):
            return np.nan
        return returns_12m - returns_1m


def calculate_momentum_6m(
    returns_6m: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    6개월 모멘텀 계산
    
    Args:
        returns_6m: 6개월 수익률
        
    Returns:
        6개월 모멘텀 (높을수록 좋음)
    """
    return returns_6m


def calculate_momentum_3m(
    returns_3m: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    3개월 모멘텀 계산
    
    Args:
        returns_3m: 3개월 수익률
        
    Returns:
        3개월 모멘텀 (높을수록 좋음)
    """
    return returns_3m


def calculate_momentum_1m(
    returns_1m: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    1개월 모멘텀 계산
    
    Args:
        returns_1m: 1개월 수익률
        
    Returns:
        1개월 모멘텀 (높을수록 좋음)
    """
    return returns_1m


def calculate_reversal_1m(
    returns_1m: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    1개월 리버설 계산 (단기 리버설 효과)
    
    공식: Reversal 1M = -1개월 수익률
    
    Args:
        returns_1m: 1개월 수익률
        
    Returns:
        1개월 리버설 (높을수록 좋음)
    """
    if isinstance(returns_1m, pd.Series):
        return -returns_1m
    else:
        return -returns_1m if pd.notna(returns_1m) else np.nan
