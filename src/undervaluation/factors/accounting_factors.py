"""
회계 품질 팩터 계산
BMad 협업으로 구현된 회계 품질 핵심 지표 계산
"""
import pandas as pd
import numpy as np
from typing import Union


def calculate_accruals(
    net_income: Union[float, pd.Series],
    operating_cash_flow: Union[float, pd.Series],
    total_assets: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    발생액률(Accruals) 계산
    
    공식: Accruals = (Net Income - Operating Cash Flow) / Total Assets
    
    Args:
        net_income: 순이익
        operating_cash_flow: 영업현금흐름
        total_assets: 총자산
        
    Returns:
        발생액률 (낮을수록 좋음)
    """
    accruals = net_income - operating_cash_flow
    
    if isinstance(accruals, pd.Series) and isinstance(total_assets, pd.Series):
        result = pd.Series(index=accruals.index, dtype=float)
        valid_mask = (accruals.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = accruals[valid_mask] / total_assets[valid_mask]
        return result
    else:
        if pd.isna(accruals) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return accruals / total_assets


def calculate_noa_ratio(
    total_assets: Union[float, pd.Series],
    cash_and_equivalents: Union[float, pd.Series]
) -> Union[float, pd.Series]:
    """
    NOA/Assets 비율 계산
    
    공식: NOA/Assets = (Total Assets - Cash) / Total Assets
    
    Args:
        total_assets: 총자산
        cash_and_equivalents: 현금및현금성자산
        
    Returns:
        NOA/Assets 비율 (낮을수록 좋음)
    """
    noa = total_assets - cash_and_equivalents
    
    if isinstance(noa, pd.Series) and isinstance(total_assets, pd.Series):
        result = pd.Series(index=noa.index, dtype=float)
        valid_mask = (noa.notna()) & (total_assets.notna()) & (total_assets != 0)
        result[valid_mask] = noa[valid_mask] / total_assets[valid_mask]
        return result
    else:
        if pd.isna(noa) or pd.isna(total_assets) or total_assets == 0:
            return np.nan
        return noa / total_assets


def calculate_risk_flags(
    interest_coverage: Union[float, pd.Series],
    debt_to_equity: Union[float, pd.Series],
    current_ratio: Union[float, pd.Series] = None
) -> Union[float, pd.Series]:
    """
    리스크 플래그 계산
    
    Args:
        interest_coverage: 이자보상배수
        debt_to_equity: 부채비율
        current_ratio: 유동비율 (선택사항)
        
    Returns:
        리스크 플래그 점수 (낮을수록 좋음)
    """
    risk_score = 0
    
    # 이자보상배수 < 2.5
    if isinstance(interest_coverage, pd.Series):
        risk_score = pd.Series(0, index=interest_coverage.index)
        risk_score[interest_coverage < 2.5] += 1
    else:
        if interest_coverage < 2.5:
            risk_score += 1
    
    # 부채비율 > 1
    if isinstance(debt_to_equity, pd.Series):
        if isinstance(risk_score, pd.Series):
            risk_score[debt_to_equity > 1] += 1
        else:
            risk_score = pd.Series(0, index=debt_to_equity.index)
            risk_score[debt_to_equity > 1] += 1
    else:
        if debt_to_equity > 1:
            risk_score += 1
    
    # 유동비율 < 1 (있는 경우)
    if current_ratio is not None:
        if isinstance(current_ratio, pd.Series):
            if isinstance(risk_score, pd.Series):
                risk_score[current_ratio < 1] += 1
            else:
                risk_score = pd.Series(0, index=current_ratio.index)
                risk_score[current_ratio < 1] += 1
        else:
            if current_ratio < 1:
                risk_score += 1
    
    return risk_score
