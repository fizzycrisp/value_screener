"""
버핏 스타일(저평가 우량주) 스크리닝 전략
기존 밸류+품질 조건을 보수적으로 결합
"""
import pandas as pd
from typing import List
import logging

from value_screener.interfaces import ScreeningStrategy, ScreenConfig


class BuffettScreeningStrategy(ScreeningStrategy):
    """버핏 스타일: 싸고(valuation) + 질 좋고(quality) + 재무 건전성"""

    def __init__(self, config: ScreenConfig = None):
        self.config = config or ScreenConfig()
        self.logger = logging.getLogger(__name__)

    def apply(self, df: pd.DataFrame, config: ScreenConfig = None) -> pd.DataFrame:
        if config is None:
            config = self.config

        self.logger.info(f"버핏 스타일 스크리닝 시작: {len(df)}개 종목")

        filters = []

        # Valuation: EV/EBIT in tight reasonable band
        if 'ev_ebit' in df.columns:
            ev_ebit_filter = (
                (df['ev_ebit'] >= max(4.0, config.ev_ebit_min)) &
                (df['ev_ebit'] <= min(12.0, config.ev_ebit_max)) &
                df['ev_ebit'].notna()
            )
            filters.append(ev_ebit_filter)

        # Valuation: FCF Yield >= 7%
        if 'fcf_yield' in df.columns:
            fcf_filter = (df['fcf_yield'] >= max(0.07, config.fcf_yield_min)) & df['fcf_yield'].notna()
            filters.append(fcf_filter)

        # Quality: ROIC >= 12%
        if 'roic' in df.columns:
            roic_filter = (df['roic'] >= max(0.12, config.roic_min)) & df['roic'].notna()
            filters.append(roic_filter)

        # Safety: Interest Coverage >= 5x
        if 'interest_coverage' in df.columns:
            ic_filter = (df['interest_coverage'] >= max(5.0, config.interest_coverage_min)) & df['interest_coverage'].notna()
            filters.append(ic_filter)

        # Safety: Net Debt / EBITDA < 1.5
        if 'net_debt_ebitda' in df.columns:
            nde_filter = (df['net_debt_ebitda'] < min(1.5, config.net_debt_to_ebitda_max)) & df['net_debt_ebitda'].notna()
            filters.append(nde_filter)

        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            df = df.copy()
            df['passed_filters'] = combined
            passed = int(combined.sum())
        else:
            df = df.copy()
            df['passed_filters'] = True
            passed = len(df)

        self.logger.info(f"버핏 스타일 스크리닝 완료: {passed}개 종목 통과")
        return df

    def get_name(self) -> str:
        return "buffett"

    def get_description(self) -> str:
        return "버핏 스타일 저평가 우량주 (EV/EBIT, FCFY, ROIC, 이자보상배수, 순부채/EBITDA)"

    def get_required_metrics(self) -> List[str]:
        return [
            'ev_ebit',
            'fcf_yield',
            'roic',
            'interest_coverage',
            'net_debt_ebitda',
        ]


