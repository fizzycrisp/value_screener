"""
의존성 주입 컨테이너
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 핵심 DI 시스템
"""
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from typing import Optional
import logging

from .interfaces import (
    DataFetcher, MetricCalculator, ScreeningStrategy, 
    CacheBackend, ReportGenerator, NotificationService,
    MetricsCollector, HealthChecker
)
from .config import ScreenConfig


class Container(containers.DeclarativeContainer):
    """메인 DI 컨테이너"""
    
    # 설정
    config = providers.Singleton(ScreenConfig)
    
    # 로깅
    logger = providers.Singleton(
        logging.getLogger,
        name="value_screener"
    )
    
    # 데이터 페처들
    yfinance_fetcher = providers.Factory(
        # 실제 구현체는 나중에 추가
        # YFinanceFetcher,
        # config=config,
        # logger=logger
    )
    
    csv_fetcher = providers.Factory(
        # CSVFetcher,
        # config=config,
        # logger=logger
    )
    
    # 지표 계산기들
    ev_ebit_calculator = providers.Factory(
        # EVEBITCalculator,
        # logger=logger
    )
    
    fcf_yield_calculator = providers.Factory(
        # FCFYieldCalculator,
        # logger=logger
    )
    
    roic_calculator = providers.Factory(
        # ROICCalculator,
        # logger=logger
    )
    
    # 스크리닝 전략들
    value_strategy = providers.Factory(
        # ValueScreeningStrategy,
        # config=config,
        # logger=logger
    )
    
    growth_strategy = providers.Factory(
        # GrowthScreeningStrategy,
        # config=config,
        # logger=logger
    )
    
    quality_strategy = providers.Factory(
        # QualityScreeningStrategy,
        # config=config,
        # logger=logger
    )
    
    # 캐시 백엔드
    cache_backend = providers.Singleton(
        # MemoryCacheBackend,
        # 또는 RedisCacheBackend
    )
    
    # 리포트 생성기
    markdown_report_generator = providers.Factory(
        # MarkdownReportGenerator,
        # logger=logger
    )
    
    csv_report_generator = providers.Factory(
        # CSVReportGenerator,
        # logger=logger
    )
    
    # 알림 서비스
    notification_service = providers.Singleton(
        # EmailNotificationService,
        # 또는 SlackNotificationService
    )
    
    # 메트릭 수집기
    metrics_collector = providers.Singleton(
        # PrometheusMetricsCollector,
        # 또는 기본 메트릭 수집기
    )
    
    # 헬스체커
    health_checker = providers.Singleton(
        # SystemHealthChecker,
        # fetchers=[yfinance_fetcher, csv_fetcher],
        # cache=cache_backend
    )


# 전역 컨테이너 인스턴스
container = Container()


def configure_container(config_path: Optional[str] = None):
    """컨테이너를 설정합니다."""
    # 설정 로드
    if config_path:
        # YAML 설정 파일에서 로드
        pass
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return container


def get_container() -> Container:
    """전역 컨테이너 인스턴스를 반환합니다."""
    return container
