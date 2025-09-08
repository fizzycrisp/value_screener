"""
성장주 투자 스크리닝 전략
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 성장주 전략 구현
"""
import pandas as pd
import numpy as np
from typing import List
import logging

from value_screener.interfaces import ScreeningStrategy, ScreenConfig


class GrowthScreeningStrategy(ScreeningStrategy):
    """성장주 투자 스크리닝 전략"""
    
    def __init__(self, config: ScreenConfig = None):
        self.config = config or ScreenConfig()
        self.logger = logging.getLogger(__name__)
    
    def apply(self, df: pd.DataFrame, config: ScreenConfig = None) -> pd.DataFrame:
        """성장주 투자 기준으로 스크리닝을 적용합니다."""
        if config is None:
            config = self.config
        
        self.logger.info(f"성장주 스크리닝 시작: {len(df)}개 종목")
        
        # 성장주 필터링 조건
        filters = []
        
        # 매출 성장률 필터 (≥15%)
        if 'revenue_growth' in df.columns:
            revenue_growth_filter = (
                (df['revenue_growth'] >= 0.15) &
                df['revenue_growth'].notna()
            )
            filters.append(revenue_growth_filter)
            self.logger.debug(f"매출 성장률 필터 통과: {revenue_growth_filter.sum()}개")
        
        # 순이익 성장률 필터 (≥20%)
        if 'net_income_growth' in df.columns:
            net_income_growth_filter = (
                (df['net_income_growth'] >= 0.20) &
                df['net_income_growth'].notna()
            )
            filters.append(net_income_growth_filter)
            self.logger.debug(f"순이익 성장률 필터 통과: {net_income_growth_filter.sum()}개")
        
        # ROE 필터 (≥15%)
        if 'roe' in df.columns:
            roe_filter = (
                (df['roe'] >= 0.15) &
                df['roe'].notna()
            )
            filters.append(roe_filter)
            self.logger.debug(f"ROE 필터 통과: {roe_filter.sum()}개")
        
        # PEG 비율 필터 (<1.5)
        if 'peg_ratio' in df.columns:
            peg_filter = (
                (df['peg_ratio'] < 1.5) &
                (df['peg_ratio'] > 0) &
                df['peg_ratio'].notna()
            )
            filters.append(peg_filter)
            self.logger.debug(f"PEG 비율 필터 통과: {peg_filter.sum()}개")
        
        # 부채비율 필터 (<50%)
        if 'debt_to_equity' in df.columns:
            debt_filter = (
                (df['debt_to_equity'] < 0.5) &
                df['debt_to_equity'].notna()
            )
            filters.append(debt_filter)
            self.logger.debug(f"부채비율 필터 통과: {debt_filter.sum()}개")
        
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
        
        self.logger.info(f"성장주 스크리닝 완료: {passed_count}개 종목 통과")
        
        return df
    
    def get_name(self) -> str:
        return "growth"
    
    def get_description(self) -> str:
        return "성장주 투자 기준 스크리닝 (매출/순이익 성장률, ROE, PEG 비율, 부채비율)"
    
    def get_required_metrics(self) -> List[str]:
        return [
            'revenue_growth',
            'net_income_growth',
            'roe',
            'peg_ratio',
            'debt_to_equity'
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
                if metric == 'revenue_growth':
                    passed = ((df[metric] >= 0.15) & df[metric].notna()).sum()
                elif metric == 'net_income_growth':
                    passed = ((df[metric] >= 0.20) & df[metric].notna()).sum()
                elif metric == 'roe':
                    passed = ((df[metric] >= 0.15) & df[metric].notna()).sum()
                elif metric == 'peg_ratio':
                    passed = ((df[metric] < 1.5) & (df[metric] > 0) & df[metric].notna()).sum()
                elif metric == 'debt_to_equity':
                    passed = ((df[metric] < 0.5) & df[metric].notna()).sum()
                else:
                    passed = df[metric].notna().sum()
                
                summary[f'{metric}_passed'] = passed
                summary[f'{metric}_pass_rate'] = passed / len(df) if len(df) > 0 else 0
        
        return summary
