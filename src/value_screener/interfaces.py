"""
Value Screener 인터페이스 정의
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 핵심 인터페이스들
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FinancialData:
    """재무 데이터를 담는 표준화된 데이터 클래스"""
    ticker: str
    name: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    
    # 손익계산서 데이터
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    pretax_income: Optional[float] = None
    income_tax_expense: Optional[float] = None
    interest_expense: Optional[float] = None
    
    # 대차대조표 데이터
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_stockholder_equity: Optional[float] = None
    
    # 현금흐름표 데이터
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    
    # 메타데이터
    last_updated: Optional[datetime] = None
    data_source: Optional[str] = None


@dataclass
class ScreenConfig:
    """스크리닝 설정을 담는 데이터 클래스"""
    ev_ebit_min: float = 5.0
    ev_ebit_max: float = 12.0
    fcf_yield_min: float = 0.07
    roic_min: float = 0.12
    interest_coverage_min: float = 4.0
    net_debt_to_ebitda_max: float = 2.0
    
    # 추가 설정
    strategy_name: str = "value"
    custom_filters: Dict[str, Any] = None


class DataFetcher(ABC):
    """데이터 페처 인터페이스"""
    
    @abstractmethod
    async def fetch_ticker_data(self, ticker: str) -> Optional[FinancialData]:
        """단일 종목의 재무 데이터를 가져옵니다."""
        pass
    
    @abstractmethod
    async def fetch_multiple_tickers(self, tickers: List[str]) -> List[FinancialData]:
        """여러 종목의 재무 데이터를 병렬로 가져옵니다."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """데이터 소스의 이름을 반환합니다."""
        pass


class MetricCalculator(ABC):
    """지표 계산기 인터페이스"""
    
    @abstractmethod
    def calculate(self, data: FinancialData) -> Optional[float]:
        """재무 데이터로부터 지표를 계산합니다."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """지표의 이름을 반환합니다."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """지표의 설명을 반환합니다."""
        pass
    
    @abstractmethod
    def get_formula(self) -> str:
        """지표의 계산 공식을 반환합니다."""
        pass


class ScreeningStrategy(ABC):
    """스크리닝 전략 인터페이스"""
    
    @abstractmethod
    def apply(self, df: pd.DataFrame, config: ScreenConfig) -> pd.DataFrame:
        """데이터프레임에 스크리닝 전략을 적용합니다."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """전략의 이름을 반환합니다."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """전략의 설명을 반환합니다."""
        pass
    
    @abstractmethod
    def get_required_metrics(self) -> List[str]:
        """이 전략에 필요한 지표 목록을 반환합니다."""
        pass


class CacheBackend(ABC):
    """캐시 백엔드 인터페이스"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값을 가져옵니다."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값을 저장합니다."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제합니다."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """캐시를 모두 지웁니다."""
        pass


class ReportGenerator(ABC):
    """리포트 생성기 인터페이스"""
    
    @abstractmethod
    def generate_report(self, results: pd.DataFrame, config: ScreenConfig) -> str:
        """분석 결과를 리포트로 생성합니다."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """지원하는 출력 형식을 반환합니다."""
        pass


class NotificationService(ABC):
    """알림 서비스 인터페이스"""
    
    @abstractmethod
    async def send_alert(self, message: str, channels: List[str]) -> bool:
        """알림을 전송합니다."""
        pass
    
    @abstractmethod
    def get_supported_channels(self) -> List[str]:
        """지원하는 알림 채널을 반환합니다."""
        pass


class MetricsCollector(ABC):
    """메트릭 수집기 인터페이스"""
    
    @abstractmethod
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """카운터를 증가시킵니다."""
        pass
    
    @abstractmethod
    def record_timing(self, name: str, duration: float, tags: Dict[str, str] = None):
        """실행 시간을 기록합니다."""
        pass
    
    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """게이지 값을 기록합니다."""
        pass


class HealthChecker(ABC):
    """헬스체크 인터페이스"""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, bool]:
        """시스템의 건강 상태를 확인합니다."""
        pass
    
    @abstractmethod
    def get_health_status(self) -> str:
        """전체 건강 상태를 반환합니다."""
        pass
