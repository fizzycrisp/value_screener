"""
유니파이드 데이터 스키마
BMad 협업으로 구현된 표준화된 데이터 스키마 시스템
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import date, datetime
import logging

from .data_models import (
    UniverseData, 
    FundamentalsData, 
    PriceData,
    FactorData,
    PortfolioData,
    validate_dataframe_schema
)


class UnifiedDataSchema:
    """유니파이드 데이터 스키마 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 필수 필드 정의
        self.required_fields = {
            'universe': [
                'ticker', 'currency', 'price', 'market_cap', 'enterprise_value',
                'total_debt', 'cash_and_equivalents', 'total_equity',
                'ebit', 'ebitda', 'gross_profit',
                'operating_cash_flow', 'capital_expenditures',
                'pretax_income', 'income_tax_expense', 'interest_expense',
                'total_assets', 'shares_outstanding', 'reporting_date'
            ],
            'fundamentals': [
                'ticker', 'ebit', 'ebitda', 'gross_profit',
                'operating_cash_flow', 'capital_expenditures',
                'pretax_income', 'income_tax_expense', 'interest_expense',
                'total_debt', 'cash_and_equivalents', 'total_equity', 'total_assets',
                'reporting_date'
            ],
            'prices': [
                'ticker', 'date', 'close'
            ]
        }
        
        # 권장 필드 정의
        self.recommended_fields = {
            'universe': [
                'sector', 'industry', 'country', 'filing_date', 'restatement_flag',
                'share_issuance', 'buyback', 'asset_growth', 'noa'
            ],
            'fundamentals': [
                'filing_date', 'restatement_flag', 'share_issuance', 'buyback'
            ],
            'prices': [
                'open', 'high', 'low', 'volume', 'adjusted_close'
            ]
        }
    
    def validate_universe_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """유니버스 데이터를 검증하고 정리합니다."""
        self.logger.info("Validating universe data schema")
        
        # 스키마 검증
        df = validate_dataframe_schema(df, UniverseData)
        
        # 통화 일관화
        df = self._normalize_currency(df)
        
        # 기업가치 계산 (없는 경우)
        df = self._calculate_enterprise_value(df)
        
        # 회계기간 정합성 확인
        df = self._validate_reporting_periods(df)
        
        self.logger.info(f"Universe data validation completed: {len(df)} records")
        return df
    
    def validate_fundamentals_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """재무 데이터를 검증하고 정리합니다."""
        self.logger.info("Validating fundamentals data schema")
        
        # 스키마 검증
        df = validate_dataframe_schema(df, FundamentalsData)
        
        # 데이터 품질 검사
        df = self._check_data_quality(df)
        
        # 이상치 탐지
        df = self._detect_outliers(df)
        
        self.logger.info(f"Fundamentals data validation completed: {len(df)} records")
        return df
    
    def validate_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """가격 데이터를 검증하고 정리합니다."""
        self.logger.info("Validating price data schema")
        
        # 스키마 검증
        df = validate_dataframe_schema(df, PriceData)
        
        # 가격 데이터 정리
        df = self._clean_price_data(df)
        
        # 수익률 계산
        df = self._calculate_returns(df)
        
        self.logger.info(f"Price data validation completed: {len(df)} records")
        return df
    
    def _normalize_currency(self, df: pd.DataFrame) -> pd.DataFrame:
        """통화를 일관화합니다."""
        if 'currency' not in df.columns:
            df['currency'] = 'USD'
        
        # 기본 통화를 USD로 설정 (환율 변환은 별도 구현 필요)
        base_currency = 'USD'
        if 'currency' in df.columns:
            non_usd_mask = df['currency'] != base_currency
            if non_usd_mask.any():
                self.logger.warning(f"Found {non_usd_mask.sum()} records with non-USD currency")
                # TODO: 환율 변환 로직 구현
        
        return df
    
    def _calculate_enterprise_value(self, df: pd.DataFrame) -> pd.DataFrame:
        """기업가치를 계산합니다 (없는 경우)."""
        if 'enterprise_value' not in df.columns:
            df['enterprise_value'] = np.nan
        
        # 기업가치가 없는 경우 계산
        missing_ev = df['enterprise_value'].isna()
        if missing_ev.any():
            required_cols = ['market_cap', 'total_debt', 'cash_and_equivalents']
            if all(col in df.columns for col in required_cols):
                df.loc[missing_ev, 'enterprise_value'] = (
                    df.loc[missing_ev, 'market_cap'] + 
                    df.loc[missing_ev, 'total_debt'] - 
                    df.loc[missing_ev, 'cash_and_equivalents']
                )
                self.logger.info(f"Calculated enterprise value for {missing_ev.sum()} records")
        
        return df
    
    def _validate_reporting_periods(self, df: pd.DataFrame) -> pd.DataFrame:
        """회계기간 정합성을 확인합니다."""
        if 'reporting_date' not in df.columns:
            return df
        
        # TTM 우선, 없으면 최근 연간 데이터 사용
        df['reporting_date'] = pd.to_datetime(df['reporting_date'])
        
        # 날짜 유효성 검사
        invalid_dates = df['reporting_date'].isna()
        if invalid_dates.any():
            self.logger.warning(f"Found {invalid_dates.sum()} records with invalid reporting dates")
        
        return df
    
    def _check_data_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 품질을 검사합니다."""
        # 0 분모 방지
        financial_columns = ['ebit', 'ebitda', 'total_assets', 'total_equity']
        for col in financial_columns:
            if col in df.columns:
                zero_mask = df[col] == 0
                if zero_mask.any():
                    self.logger.warning(f"Found {zero_mask.sum()} records with zero {col}")
        
        # 음수 값 검사
        positive_columns = ['market_cap', 'total_assets', 'total_equity']
        for col in positive_columns:
            if col in df.columns:
                negative_mask = df[col] < 0
                if negative_mask.any():
                    self.logger.warning(f"Found {negative_mask.sum()} records with negative {col}")
        
        return df
    
    def _detect_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """이상치를 탐지합니다."""
        # 전기 대비 급변 탐지 (±200%)
        financial_columns = ['ebit', 'ebitda', 'total_assets']
        for col in financial_columns:
            if col in df.columns:
                # 간단한 이상치 탐지 (IQR 방법)
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                if outliers.any():
                    self.logger.warning(f"Found {outliers.sum()} outliers in {col}")
        
        return df
    
    def _clean_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """가격 데이터를 정리합니다."""
        # 가격 데이터 정리
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in df.columns:
                # 음수 가격 제거
                negative_mask = df[col] < 0
                if negative_mask.any():
                    df.loc[negative_mask, col] = np.nan
                    self.logger.warning(f"Removed {negative_mask.sum()} negative {col} values")
        
        # OHLC 논리 검사
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            invalid_ohlc = (
                (df['high'] < df['low']) |
                (df['high'] < df['open']) |
                (df['high'] < df['close']) |
                (df['low'] > df['open']) |
                (df['low'] > df['close'])
            )
            if invalid_ohlc.any():
                self.logger.warning(f"Found {invalid_ohlc.sum()} records with invalid OHLC data")
        
        return df
    
    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """수익률을 계산합니다."""
        if 'close' not in df.columns:
            return df
        
        # 티커별로 정렬
        df = df.sort_values(['ticker', 'date'])
        
        # 일일 수익률 계산
        df['daily_return'] = df.groupby('ticker')['close'].pct_change()
        
        # 누적 수익률 계산
        df['cumulative_return'] = df.groupby('ticker')['daily_return'].apply(
            lambda x: (1 + x).cumprod() - 1
        )
        
        return df
    
    def get_schema_summary(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """스키마 요약 정보를 반환합니다."""
        summary = {
            'data_type': data_type,
            'total_records': len(df),
            'total_columns': len(df.columns),
            'required_fields_present': [],
            'required_fields_missing': [],
            'recommended_fields_present': [],
            'recommended_fields_missing': [],
            'data_quality': {}
        }
        
        if data_type in self.required_fields:
            required = self.required_fields[data_type]
            summary['required_fields_present'] = [col for col in required if col in df.columns]
            summary['required_fields_missing'] = [col for col in required if col not in df.columns]
        
        if data_type in self.recommended_fields:
            recommended = self.recommended_fields[data_type]
            summary['recommended_fields_present'] = [col for col in recommended if col in df.columns]
            summary['recommended_fields_missing'] = [col for col in recommended if col not in df.columns]
        
        # 데이터 품질 지표
        summary['data_quality'] = {
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_records': df.duplicated().sum(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }
        
        return summary


def validate_data_schema(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """데이터 스키마를 검증합니다."""
    schema = UnifiedDataSchema()
    
    if data_type == 'universe':
        return schema.validate_universe_data(df)
    elif data_type == 'fundamentals':
        return schema.validate_fundamentals_data(df)
    elif data_type == 'prices':
        return schema.validate_price_data(df)
    else:
        raise ValueError(f"Unknown data type: {data_type}")
