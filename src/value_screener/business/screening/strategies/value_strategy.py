"""
밸류 투자 스크리닝 전략
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 핵심 전략 구현
"""
import pandas as pd
import numpy as np
from typing import List
import logging

from value_screener.interfaces import ScreeningStrategy, ScreenConfig


class ValueScreeningStrategy(ScreeningStrategy):
    """밸류 투자 스크리닝 전략"""
    
    def __init__(self, config: ScreenConfig = None):
        self.config = config or ScreenConfig()
        self.logger = logging.getLogger(__name__)
    
    def apply(self, df: pd.DataFrame, config: ScreenConfig = None) -> pd.DataFrame:
        """밸류 투자 기준으로 스크리닝을 적용합니다."""
        if config is None:
            config = self.config
        
        self.logger.info(f"밸류 스크리닝 시작: {len(df)}개 종목")
        
        # 필터링 조건 적용
        filters = []
        
        # EV/EBIT 필터 (5-12 범위)
        if 'ev_ebit' in df.columns:
            ev_ebit_filter = (
                (df['ev_ebit'] >= config.ev_ebit_min) & 
                (df['ev_ebit'] <= config.ev_ebit_max) &
                df['ev_ebit'].notna()
            )
            filters.append(ev_ebit_filter)
            self.logger.debug(f"EV/EBIT 필터 통과: {ev_ebit_filter.sum()}개")
        
        # FCF 수익률 필터 (≥7%)
        if 'fcf_yield' in df.columns:
            fcf_yield_filter = (
                (df['fcf_yield'] >= config.fcf_yield_min) &
                df['fcf_yield'].notna()
            )
            filters.append(fcf_yield_filter)
            self.logger.debug(f"FCF 수익률 필터 통과: {fcf_yield_filter.sum()}개")
        
        # ROIC 필터 (≥12%)
        if 'roic' in df.columns:
            roic_filter = (
                (df['roic'] >= config.roic_min) &
                df['roic'].notna()
            )
            filters.append(roic_filter)
            self.logger.debug(f"ROIC 필터 통과: {roic_filter.sum()}개")
        
        # 이자보상배수 필터 (≥4배)
        if 'interest_coverage' in df.columns:
            interest_coverage_filter = (
                (df['interest_coverage'] >= config.interest_coverage_min) &
                df['interest_coverage'].notna()
            )
            filters.append(interest_coverage_filter)
            self.logger.debug(f"이자보상배수 필터 통과: {interest_coverage_filter.sum()}개")
        
        # 순부채/EBITDA 필터 (<2)
        if 'net_debt_ebitda' in df.columns:
            net_debt_filter = (
                (df['net_debt_ebitda'] < config.net_debt_to_ebitda_max) &
                df['net_debt_ebitda'].notna()
            )
            filters.append(net_debt_filter)
            self.logger.debug(f"순부채/EBITDA 필터 통과: {net_debt_filter.sum()}개")
        
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
        
        self.logger.info(f"밸류 스크리닝 완료: {passed_count}개 종목 통과")
        
        return df
    
    def get_name(self) -> str:
        return "value"
    
    def get_description(self) -> str:
        return "밸류 투자 기준 스크리닝 (EV/EBIT, FCF 수익률, ROIC, 이자보상배수, 순부채/EBITDA)"
    
    def get_required_metrics(self) -> List[str]:
        return [
            'ev_ebit',
            'fcf_yield', 
            'roic',
            'interest_coverage',
            'net_debt_ebitda'
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
                if metric == 'ev_ebit':
                    passed = (
                        (df[metric] >= self.config.ev_ebit_min) & 
                        (df[metric] <= self.config.ev_ebit_max) &
                        df[metric].notna()
                    ).sum()
                elif metric == 'fcf_yield':
                    passed = (
                        (df[metric] >= self.config.fcf_yield_min) &
                        df[metric].notna()
                    ).sum()
                elif metric == 'roic':
                    passed = (
                        (df[metric] >= self.config.roic_min) &
                        df[metric].notna()
                    ).sum()
                elif metric == 'interest_coverage':
                    passed = (
                        (df[metric] >= self.config.interest_coverage_min) &
                        df[metric].notna()
                    ).sum()
                elif metric == 'net_debt_ebitda':
                    passed = (
                        (df[metric] < self.config.net_debt_to_ebitda_max) &
                        df[metric].notna()
                    ).sum()
                else:
                    passed = df[metric].notna().sum()
                
                summary[f'{metric}_passed'] = passed
                summary[f'{metric}_pass_rate'] = passed / len(df) if len(df) > 0 else 0
        
        return summary
