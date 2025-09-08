"""
스크리닝 전략 팩토리
BMad 아키텍트 에이전트가 설계한 확장 가능한 아키텍처의 전략 팩토리 구현
"""
from typing import Dict, Type
from dependency_injector.wiring import inject, Provide

from .strategies import (
    ValueScreeningStrategy,
    GrowthScreeningStrategy, 
    QualityScreeningStrategy
)
from value_screener.interfaces import ScreeningStrategy


class StrategyFactory:
    """스크리닝 전략 팩토리"""
    
    _strategies: Dict[str, Type[ScreeningStrategy]] = {
        'value': ValueScreeningStrategy,
        'growth': GrowthScreeningStrategy,
        'quality': QualityScreeningStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str) -> ScreeningStrategy:
        """전략 이름으로 스크리닝 전략을 생성합니다."""
        if strategy_name not in cls._strategies:
            available_strategies = list(cls._strategies.keys())
            raise ValueError(
                f"지원하지 않는 전략입니다: {strategy_name}. "
                f"사용 가능한 전략: {available_strategies}"
            )
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class()
    
    @classmethod
    def get_available_strategies(cls) -> Dict[str, str]:
        """사용 가능한 전략 목록과 설명을 반환합니다."""
        strategies = {}
        for name, strategy_class in cls._strategies.items():
            # 임시 인스턴스를 생성하여 설명을 가져옴
            temp_instance = strategy_class()
            strategies[name] = temp_instance.get_description()
        return strategies
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[ScreeningStrategy]):
        """새로운 전략을 등록합니다."""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get_strategy_requirements(cls, strategy_name: str) -> list:
        """전략에 필요한 지표 목록을 반환합니다."""
        if strategy_name not in cls._strategies:
            raise ValueError(f"지원하지 않는 전략입니다: {strategy_name}")
        
        strategy_class = cls._strategies[strategy_name]
        temp_instance = strategy_class()
        return temp_instance.get_required_metrics()
