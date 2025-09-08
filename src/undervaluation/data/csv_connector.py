"""
CSV 데이터 커넥터
BMad 협업으로 구현된 CSV 기반 데이터 소스
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging
import os

from .interfaces import DataConnector


class CSVConnector(DataConnector):
    """CSV 데이터 커넥터"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.file_path = config.get('file_path')
        
        if not self.file_path or not os.path.exists(self.file_path):
            raise ValueError(f"CSV file not found: {self.file_path}")
    
    def get_name(self) -> str:
        return "csv"
    
    def fetch_universe(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """유니버스 데이터를 가져옵니다."""
        self.logger.info(f"Loading universe data from CSV: {self.file_path}")
        
        try:
            df = pd.read_csv(self.file_path)
            
            # 필수 컬럼 확인
            required_columns = ['ticker']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # 티커 필터링
            if tickers:
                df = df[df['ticker'].isin(tickers)]
            
            # 기본 컬럼 추가
            if 'currency' not in df.columns:
                df['currency'] = 'USD'
            if 'reporting_date' not in df.columns:
                df['reporting_date'] = asof
            if 'data_source' not in df.columns:
                df['data_source'] = 'csv'
            
            self.logger.info(f"Loaded universe data for {len(df)} tickers")
            return df
            
        except Exception as e:
            self._handle_error(e)
            return pd.DataFrame()
    
    def fetch_fundamentals(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """재무 데이터를 가져옵니다."""
        self.logger.info(f"Loading fundamentals from CSV: {self.file_path}")
        
        try:
            df = pd.read_csv(self.file_path)
            
            # 필수 컬럼 확인
            required_columns = ['ticker']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # 티커 필터링
            if tickers:
                df = df[df['ticker'].isin(tickers)]
            
            # 기본 컬럼 추가
            if 'reporting_date' not in df.columns:
                df['reporting_date'] = asof
            if 'data_source' not in df.columns:
                df['data_source'] = 'csv'
            
            # 재무 데이터 컬럼 확인 및 기본값 설정
            financial_columns = [
                'ebit', 'ebitda', 'gross_profit', 'pretax_income', 
                'income_tax_expense', 'interest_expense',
                'total_debt', 'cash_and_equivalents', 'total_equity', 'total_assets',
                'operating_cash_flow', 'capital_expenditures'
            ]
            
            for col in financial_columns:
                if col not in df.columns:
                    df[col] = np.nan
            
            self.logger.info(f"Loaded fundamentals for {len(df)} tickers")
            return df
            
        except Exception as e:
            self._handle_error(e)
            return pd.DataFrame()
    
    def fetch_prices(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        """가격 데이터를 가져옵니다."""
        self.logger.info(f"Loading prices from CSV: {self.file_path}")
        
        try:
            df = pd.read_csv(self.file_path)
            
            # 필수 컬럼 확인
            required_columns = ['ticker', 'date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # 날짜 컬럼 변환
            df['date'] = pd.to_datetime(df['date'])
            
            # 날짜 필터링
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            
            # 티커 필터링
            if tickers:
                df = df[df['ticker'].isin(tickers)]
            
            # 가격 컬럼 확인
            price_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in price_columns:
                if col not in df.columns:
                    df[col] = np.nan
            
            self.logger.info(f"Loaded price data for {len(df)} records")
            return df
            
        except Exception as e:
            self._handle_error(e)
            return pd.DataFrame()
    
    def validate_schema(self) -> Dict[str, Any]:
        """CSV 스키마를 검증합니다."""
        try:
            df = pd.read_csv(self.file_path, nrows=1)
            
            # 필수 컬럼 확인
            required_columns = [
                'ticker', 'currency', 'price', 'market_cap', 'enterprise_value',
                'total_debt', 'cash_and_equivalents', 'total_equity',
                'ebit', 'ebitda', 'gross_profit',
                'operating_cash_flow', 'capital_expenditures',
                'pretax_income', 'income_tax_expense', 'interest_expense',
                'total_assets', 'shares_outstanding', 'reporting_date'
            ]
            
            available_columns = list(df.columns)
            missing_columns = [col for col in required_columns if col not in available_columns]
            optional_columns = [col for col in available_columns if col not in required_columns]
            
            return {
                'valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'optional_columns': optional_columns,
                'total_columns': len(available_columns)
            }
            
        except Exception as e:
            self._handle_error(e)
            return {
                'valid': False,
                'error': str(e),
                'missing_columns': [],
                'optional_columns': [],
                'total_columns': 0
            }
