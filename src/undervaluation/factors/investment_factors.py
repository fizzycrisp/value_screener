"""
투자/발행 팩터 계산
BMad 협업으로 구현된 투자 및 발행 관련 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Union


def calculate_asset_growth(
    current_assets: Union[float, pd.Series],
    previous_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    자산 성장률 계산
    
    공식: Asset Growth = (Current Assets - Previous Assets) / Previous Assets
    
    Args:
        current_assets: 현재 자산
        previous_assets: 이전 자산
        
    Returns:
        자산 성장률 (낮을수록 좋음)
    """
    if isinstance(current_assets, pd.Series) and isinstance(previous_assets, pd.Series):
        result = pd.Series(index=current_assets.index, dtype=float)
        valid_mask = (current_assets.notna()) & (previous_assets.notna()) & (previous_assets != 0)
        result[valid_mask] = (current_assets[valid_mask] - previous_assets[valid_mask]) / previous_assets[valid_mask]
        return result
    else:
        if pd.isna(current_assets) or pd.isna(previous_assets) or previous_assets == 0:
            return np.nan
        return (current_assets - previous_assets) / previous_assets


def calculate_net_issuance(
    shares_outstanding_current: Union[float, pd.Series],
    shares_outstanding_previous: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    순발행률 계산
    
    공식: Net Issuance = (Current Shares - Previous Shares) / Previous Shares
    
    Args:
        shares_outstanding_current: 현재 발행주식수
        shares_outstanding_previous: 이전 발행주식수
        
    Returns:
        순발행률 (낮을수록 좋음)
    """
    if isinstance(shares_outstanding_current, pd.Series) and isinstance(shares_outstanding_previous, pd.Series):
        result = pd.Series(index=shares_outstanding_current.index, dtype=float)
        valid_mask = (shares_outstanding_current.notna()) & (shares_outstanding_previous.notna()) & (shares_outstanding_previous != 0)
        result[valid_mask] = (shares_outstanding_current[valid_mask] - shares_outstanding_previous[valid_mask]) / shares_outstanding_previous[valid_mask]
        return result
    else:
        if pd.isna(shares_outstanding_current) or pd.isna(shares_outstanding_previous) or shares_outstanding_previous == 0:
            return np.nan
        return (shares_outstanding_current - shares_outstanding_previous) / shares_outstanding_previous


def calculate_capex_intensity(
    capital_expenditures: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    자본지출 강도 계산
    
    공식: CapEx Intensity = |Capital Expenditures| / Total Assets
    
    Args:
        capital_expenditures: 자본지출
        total_assets: 총자산
        
    Returns:
        자본지출 강도 (낮을수록 좋음)
    """
    abs_capex = np.abs(capital_expenditures)
    
    if isinstance(abs_capex, pd.Series) and isinstance(total_assets, pd.Series):
        result = pd.Series(index=abs_capex.index, dtype=float)
        valid_mask = (abs_capex.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = abs_capex[valid_mask] / total_assets[valid_mask]
        return result
    else:
        if pd.isna(abs_capex) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return abs_capex / total_assets


def calculate_rd_intensity(
    rd_expense: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    R&D 강도 계산
    
    공식: R&D Intensity = R&D Expense / Total Assets
    
    Args:
        rd_expense: R&D 비용
        total_assets: 총자산
        
    Returns:
        R&D 강도 (높을수록 좋음)
    """
    if isinstance(rd_expense, pd.Series) and isinstance(total_assets, pd.Series):
        result = pd.Series(index=rd_expense.index, dtype=float)
        valid_mask = (rd_expense.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = rd_expense[valid_mask] / total_assets[valid_mask]
        return result
    else:
        if pd.isna(rd_expense) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return rd_expense / total_assets
