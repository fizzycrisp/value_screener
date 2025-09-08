"""
YFinance 데이터 커넥터
BMad 협업으로 구현된 yfinance 기반 데이터 소스
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .interfaces import DataConnector


class YFinanceConnector(DataConnector):
    """YFinance 데이터 커넥터"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # yfinance 설정
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """yfinance 세션을 설정합니다."""
        # yfinance가 자체적으로 세션을 관리하도록 함
        self.session = None
    
    def get_name(self) -> str:
        return "yfinance"
    
    def fetch_universe(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """유니버스 데이터를 가져옵니다."""
        self.logger.info(f"Fetching universe data for {len(tickers)} tickers")
        
        valid_tickers = self.validate_tickers(tickers)
        if not valid_tickers:
            self.logger.warning("No valid tickers provided")
            return pd.DataFrame()
        
        # 병렬로 데이터 가져오기
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_ticker = {
                executor.submit(self._fetch_single_universe, ticker, asof): ticker 
                for ticker in valid_tickers
            }
            
            for future in tqdm(as_completed(future_to_ticker), 
                             total=len(valid_tickers), 
                             desc="Fetching universe data"):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self._handle_error(e, ticker)
        
        if not results:
            self.logger.warning("No universe data retrieved")
            return pd.DataFrame()
        
        df = pd.concat(results, ignore_index=True)
        self.logger.info(f"Retrieved universe data for {len(df)} tickers")
        return df
    
    def fetch_fundamentals(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """재무 데이터를 가져옵니다."""
        self.logger.info(f"Fetching fundamentals for {len(tickers)} tickers")
        
        valid_tickers = self.validate_tickers(tickers)
        if not valid_tickers:
            self.logger.warning("No valid tickers provided")
            return pd.DataFrame()
        
        # 병렬로 데이터 가져오기
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:  # 재무 데이터는 더 적은 워커 사용
            future_to_ticker = {
                executor.submit(self._fetch_single_fundamentals, ticker, asof): ticker 
                for ticker in valid_tickers
            }
            
            for future in tqdm(as_completed(future_to_ticker), 
                             total=len(valid_tickers), 
                             desc="Fetching fundamentals"):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self._handle_error(e, ticker)
        
        if not results:
            self.logger.warning("No fundamentals data retrieved")
            return pd.DataFrame()
        
        df = pd.concat(results, ignore_index=True)
        self.logger.info(f"Retrieved fundamentals for {len(df)} tickers")
        return df
    
    def fetch_prices(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        """가격 데이터를 가져옵니다."""
        self.logger.info(f"Fetching prices for {len(tickers)} tickers from {start} to {end}")
        
        valid_tickers = self.validate_tickers(tickers)
        if not valid_tickers:
            self.logger.warning("No valid tickers provided")
            return pd.DataFrame()
        
        # 병렬로 데이터 가져오기
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_ticker = {
                executor.submit(self._fetch_single_prices, ticker, start, end): ticker 
                for ticker in valid_tickers
            }
            
            for future in tqdm(as_completed(future_to_ticker), 
                             total=len(valid_tickers), 
                             desc="Fetching prices"):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self._handle_error(e, ticker)
        
        if not results:
            self.logger.warning("No price data retrieved")
            return pd.DataFrame()
        
        df = pd.concat(results, ignore_index=True)
        self.logger.info(f"Retrieved price data for {len(df)} tickers")
        return df
    
    def _fetch_single_universe(self, ticker: str, asof: date) -> Optional[pd.DataFrame]:
        """단일 티커의 유니버스 데이터를 가져옵니다."""
        try:
            self._apply_rate_limit()
            
            stock = yf.Ticker(ticker, session=self.session)
            info = stock.info
            
            # 기본 정보 추출
            data = {
                'ticker': ticker,
                'currency': info.get('currency', 'USD'),
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country'),
                'reporting_date': asof,
                'data_source': 'yfinance'
            }
            
            # None 값들을 NaN으로 변환
            for key, value in data.items():
                if value is None:
                    data[key] = np.nan
            
            return pd.DataFrame([data])
            
        except Exception as e:
            self._handle_error(e, ticker)
            return None
    
    def _fetch_single_fundamentals(self, ticker: str, asof: date) -> Optional[pd.DataFrame]:
        """단일 티커의 재무 데이터를 가져옵니다."""
        try:
            self._apply_rate_limit()
            
            stock = yf.Ticker(ticker, session=self.session)
            
            # 재무제표 데이터 가져오기
            income_stmt = stock.income_stmt
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # 최신 연간 데이터 사용 (TTM 우선, 없으면 최근 연간)
            latest_date = None
            if not income_stmt.empty:
                latest_date = income_stmt.columns[0]
            
            data = {
                'ticker': ticker,
                'reporting_date': asof,
                'data_source': 'yfinance'
            }
            
            # 손익계산서 데이터
            if not income_stmt.empty:
                data.update({
                    'ebit': self._get_latest_value(income_stmt, 'EBIT'),
                    'ebitda': self._get_latest_value(income_stmt, 'EBITDA'),
                    'gross_profit': self._get_latest_value(income_stmt, 'Gross Profit'),
                    'pretax_income': self._get_latest_value(income_stmt, 'Pretax Income'),
                    'income_tax_expense': self._get_latest_value(income_stmt, 'Tax Provision'),
                    'interest_expense': self._get_latest_value(income_stmt, 'Interest Expense')
                })
            
            # 대차대조표 데이터
            if not balance_sheet.empty:
                data.update({
                    'total_debt': self._get_latest_value(balance_sheet, 'Total Debt'),
                    'cash_and_equivalents': self._get_latest_value(balance_sheet, 'Cash And Cash Equivalents'),
                    'total_equity': self._get_latest_value(balance_sheet, 'Stockholders Equity'),
                    'total_assets': self._get_latest_value(balance_sheet, 'Total Assets')
                })
            
            # 현금흐름표 데이터
            if not cashflow.empty:
                data.update({
                    'operating_cash_flow': self._get_latest_value(cashflow, 'Operating Cash Flow'),
                    'capital_expenditures': self._get_latest_value(cashflow, 'Capital Expenditures')
                })
            
            # None 값들을 NaN으로 변환
            for key, value in data.items():
                if value is None:
                    data[key] = np.nan
            
            return pd.DataFrame([data])
            
        except Exception as e:
            self._handle_error(e, ticker)
            return None
    
    def _fetch_single_prices(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        """단일 티커의 가격 데이터를 가져옵니다."""
        try:
            self._apply_rate_limit()
            
            stock = yf.Ticker(ticker, session=self.session)
            hist = stock.history(start=start, end=end)
            
            if hist.empty:
                return None
            
            # 데이터 정리
            hist = hist.reset_index()
            hist['ticker'] = ticker
            hist['date'] = hist['Date']
            hist = hist.drop('Date', axis=1)
            
            # 필요한 컬럼만 선택
            price_columns = ['ticker', 'date', 'Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in price_columns if col in hist.columns]
            hist = hist[available_columns]
            
            return hist
            
        except Exception as e:
            self._handle_error(e, ticker)
            return None
    
    def _get_latest_value(self, df: pd.DataFrame, key: str) -> Optional[float]:
        """DataFrame에서 최신 값을 가져옵니다."""
        try:
            if key in df.index:
                # TTM 데이터 우선
                for col in df.columns:
                    value = df.loc[key, col]
                    if pd.notna(value) and value != 0:
                        return float(value)
            return None
        except (KeyError, ValueError, TypeError):
            return None
