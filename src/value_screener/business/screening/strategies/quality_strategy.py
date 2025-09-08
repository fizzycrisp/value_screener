"""
품질주 투자 스크리닝 전략
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 품질주 전략 구현
"""
import pandas as pd
import numpy as np
from typing import List
import logging

from value_screener.interfaces import ScreeningStrategy, ScreenConfig


class QualityScreeningStrategy(ScreeningStrategy):
    """품질주 투자 스크리닝 전략"""
    
    def __init__(self, config: ScreenConfig = None):
        self.config = config or ScreenConfig()
        self.logger = logging.getLogger(__name__)
    
    def apply(self, df: pd.DataFrame, config: ScreenConfig = None) -> pd.DataFrame:
        """품질주 투자 기준으로 스크리닝을 적용합니다."""
        if config is None:
            config = self.config
        
        self.logger.info(f"품질주 스크리닝 시작: {len(df)}개 종목")
        
        # 품질주 필터링 조건
        filters = []
        
        # ROIC 필터 (≥15%)
        if 'roic' in df.columns:
            roic_filter = (
                (df['roic'] >= 0.15) &
                df['roic'].notna()
            )
            filters.append(roic_filter)
            self.logger.debug(f"ROIC 필터 통과: {roic_filter.sum()}개")
        
        # ROE 필터 (≥15%)
        if 'roe' in df.columns:
            roe_filter = (
                (df['roe'] >= 0.15) &
                df['roe'].notna()
            )
            filters.append(roe_filter)
            self.logger.debug(f"ROE 필터 통과: {roe_filter.sum()}개")
        
        # 이자보상배수 필터 (≥5배)
        if 'interest_coverage' in df.columns:
            interest_coverage_filter = (
                (df['interest_coverage'] >= 5.0) &
                df['interest_coverage'].notna()
            )
            filters.append(interest_coverage_filter)
            self.logger.debug(f"이자보상배수 필터 통과: {interest_coverage_filter.sum()}개")
        
        # 순부채/EBITDA 필터 (<1.5)
        if 'net_debt_ebitda' in df.columns:
            net_debt_filter = (
                (df['net_debt_ebitda'] < 1.5) &
                df['net_debt_ebitda'].notna()
            )
            filters.append(net_debt_filter)
            self.logger.debug(f"순부채/EBITDA 필터 통과: {net_debt_filter.sum()}개")
        
        # FCF 수익률 필터 (≥8%)
        if 'fcf_yield' in df.columns:
            fcf_yield_filter = (
                (df['fcf_yield'] >= 0.08) &
                df['fcf_yield'].notna()
            )
            filters.append(fcf_yield_filter)
            self.logger.debug(f"FCF 수익률 필터 통과: {fcf_yield_filter.sum()}개")
        
        # 매출 안정성 필터 (5년간 매출 변동성 <20%)
        if 'revenue_volatility' in df.columns:
            revenue_stability_filter = (
                (df['revenue_volatility'] < 0.20) &
                df['revenue_volatility'].notna()
            )
            filters.append(revenue_stability_filter)
            self.logger.debug(f"매출 안정성 필터 통과: {revenue_stability_filter.sum()}개")
        
        # 모든 필터를 결합
        if filters:
            combined_filter = filters[0]
            for filter_condition in filters[1:]:
                combined_filter = combined_filter & filter_condition
            
            df['passed_filters'] = combined_filter
            passed_count = combined_filter.sum()
        else:
            df['passed_filters'] = True
            passed_count = len(df)
        
        self.logger.info(f"품질주 스크리닝 완료: {passed_count}개 종목 통과")
        
        return df
    
    def get_name(self) -> str:
        return "quality"
    
    def get_description(self) -> str:
        return "품질주 투자 기준 스크리닝 (ROIC, ROE, 이자보상배수, 순부채/EBITDA, FCF 수익률, 매출 안정성)"
    
    def get_required_metrics(self) -> List[str]:
        return [
            'roic',
            'roe',
            'interest_coverage',
            'net_debt_ebitda',
            'fcf_yield',
            'revenue_volatility'
        ]
    
    def get_filter_summary(self, df: pd.DataFrame) -> dict:
        """필터별 통과 현황을 요약합니다."""
        summary = {
            'total_stocks': len(df),
            'passed_all_filters': df.get('passed_filters', pd.Series([False] * len(df))).sum()
        }
        
        # 각 지표별 통과 현황
        metrics = self.get_required_metrics()
        for metric in metrics:
            if metric in df.columns:
                if metric == 'roic':
                    passed = ((df[metric] >= 0.15) & df[metric].notna()).sum()
                elif metric == 'roe':
                    passed = ((df[metric] >= 0.15) & df[metric].notna()).sum()
                elif metric == 'interest_coverage':
                    passed = ((df[metric] >= 5.0) & df[metric].notna()).sum()
                elif metric == 'net_debt_ebitda':
                    passed = ((df[metric] < 1.5) & df[metric].notna()).sum()
                elif metric == 'fcf_yield':
                    passed = ((df[metric] >= 0.08) & df[metric].notna()).sum()
                elif metric == 'revenue_volatility':
                    passed = ((df[metric] < 0.20) & df[metric].notna()).sum()
                else:
                    passed = df[metric].notna().sum()
                
                summary[f'{metric}_passed'] = passed
                summary[f'{metric}_pass_rate'] = passed / len(df) if len(df) > 0 else 0
        
        return summary
