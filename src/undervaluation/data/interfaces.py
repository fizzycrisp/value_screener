"""
데이터 소스 인터페이스 정의
BMad 협업으로 구현된 확장 가능한 데이터 소스 시스템의 핵심 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict, Any
import pandas as pd
from datetime import date, datetime


class DataSource(Protocol):
    """데이터 소스 프로토콜"""
    
    def fetch_universe(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """유니버스 데이터를 가져옵니다."""
        ...
    
    def fetch_fundamentals(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """재무 데이터를 가져옵니다."""
        ...
    
    def fetch_prices(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        """가격 데이터를 가져옵니다."""
        ...


class DataConnector(ABC):
    """데이터 커넥터 추상 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 10.0)
        self.max_retries = config.get('max_retries', 3)
        self.rate_limit = config.get('rate_limit', 0.1)
    
    @abstractmethod
    def fetch_universe(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """유니버스 데이터를 가져옵니다."""
        pass
    
    @abstractmethod
    def fetch_fundamentals(self, tickers: List[str], asof: date) -> pd.DataFrame:
        """재무 데이터를 가져옵니다."""
        pass
    
    @abstractmethod
    def fetch_prices(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        """가격 데이터를 가져옵니다."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """커넥터 이름을 반환합니다."""
        pass
    
    def validate_tickers(self, tickers: List[str]) -> List[str]:
        """티커 유효성을 검증합니다."""
        valid_tickers = []
        for ticker in tickers:
            if self._is_valid_ticker(ticker):
                valid_tickers.append(ticker)
        return valid_tickers
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """티커 형식이 유효한지 확인합니다."""
        if not ticker or not isinstance(ticker, str):
            return False
        
        # 기본적인 티커 형식 검증
        ticker = ticker.strip().upper()
        if len(ticker) < 1 or len(ticker) > 20:
            return False
        
        # 특수 문자 제외
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-')
        if not all(c in allowed_chars for c in ticker):
            return False
        
        return True
    
    def _handle_error(self, error: Exception, ticker: str = None) -> None:
        """에러를 처리하고 로깅합니다."""
        import logging
        logger = logging.getLogger(__name__)
        
        if ticker:
            logger.warning(f"Error fetching data for {ticker}: {error}")
        else:
            logger.error(f"Data connector error: {error}")
    
    def _apply_rate_limit(self) -> None:
        """레이트 리밋을 적용합니다."""
        import time
        time.sleep(self.rate_limit)
