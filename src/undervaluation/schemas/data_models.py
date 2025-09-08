"""
데이터 모델 정의
BMad 협업으로 구현된 Pydantic 기반 데이터 검증 모델
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd
import numpy as np


class UniverseData(BaseModel):
    """유니버스 데이터 모델"""
    ticker: str = Field(..., description="종목 코드")
    currency: str = Field(default="USD", description="통화")
    price: Optional[float] = Field(None, description="현재 가격")
    market_cap: Optional[float] = Field(None, description="시가총액")
    enterprise_value: Optional[float] = Field(None, description="기업가치")
    shares_outstanding: Optional[float] = Field(None, description="발행주식수")
    sector: Optional[str] = Field(None, description="섹터")
    industry: Optional[str] = Field(None, description="업종")
    country: Optional[str] = Field(None, description="국가")
    reporting_date: date = Field(..., description="보고일")
    data_source: str = Field(..., description="데이터 소스")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()
    
    @validator('price', 'market_cap', 'enterprise_value', 'shares_outstanding')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be positive')
        return v


class FundamentalsData(BaseModel):
    """재무 데이터 모델"""
    ticker: str = Field(..., description="종목 코드")
    
    # 손익계산서
    ebit: Optional[float] = Field(None, description="EBIT")
    ebitda: Optional[float] = Field(None, description="EBITDA")
    gross_profit: Optional[float] = Field(None, description="매출총이익")
    pretax_income: Optional[float] = Field(None, description="세전이익")
    income_tax_expense: Optional[float] = Field(None, description="법인세비용")
    interest_expense: Optional[float] = Field(None, description="이자비용")
    
    # 대차대조표
    total_debt: Optional[float] = Field(None, description="총부채")
    cash_and_equivalents: Optional[float] = Field(None, description="현금및현금성자산")
    total_equity: Optional[float] = Field(None, description="총자본")
    total_assets: Optional[float] = Field(None, description="총자산")
    
    # 현금흐름표
    operating_cash_flow: Optional[float] = Field(None, description="영업현금흐름")
    capital_expenditures: Optional[float] = Field(None, description="자본지출")
    
    # 메타데이터
    reporting_date: date = Field(..., description="보고일")
    filing_date: Optional[date] = Field(None, description="공시일")
    restatement_flag: Optional[bool] = Field(None, description="정정공시 여부")
    data_source: str = Field(..., description="데이터 소스")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()


class PriceData(BaseModel):
    """가격 데이터 모델"""
    ticker: str = Field(..., description="종목 코드")
    price_date: date = Field(..., description="날짜")
    open_price: Optional[float] = Field(None, description="시가")
    high_price: Optional[float] = Field(None, description="고가")
    low_price: Optional[float] = Field(None, description="저가")
    close_price: Optional[float] = Field(None, description="종가")
    volume: Optional[float] = Field(None, description="거래량")
    adjusted_close: Optional[float] = Field(None, description="수정종가")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()
    
    @validator('open_price', 'high_price', 'low_price', 'close_price', 'volume', 'adjusted_close')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price and volume must be positive')
        return v


class FactorData(BaseModel):
    """팩터 데이터 모델"""
    ticker: str = Field(..., description="종목 코드")
    asof_date: date = Field(..., description="기준일")
    
    # 밸류 팩터
    earnings_yield: Optional[float] = Field(None, description="수익률")
    fcf_yield: Optional[float] = Field(None, description="FCF 수익률")
    book_to_market: Optional[float] = Field(None, description="B/M 비율")
    
    # 퀄리티 팩터
    gross_profitability: Optional[float] = Field(None, description="매출총이익률")
    roic: Optional[float] = Field(None, description="ROIC")
    f_score: Optional[float] = Field(None, description="F-Score")
    
    # 회계 품질 팩터
    accruals: Optional[float] = Field(None, description="발생액률")
    noa_ratio: Optional[float] = Field(None, description="NOA/Assets")
    risk_flags: Optional[float] = Field(None, description="리스크 플래그")
    
    # 투자/발행 팩터
    asset_growth: Optional[float] = Field(None, description="자산 성장률")
    net_issuance: Optional[float] = Field(None, description="순발행률")
    
    # 모멘텀 팩터
    momentum_12m_1m: Optional[float] = Field(None, description="12-1 모멘텀")
    
    # 정규화된 팩터
    normalized_score: Optional[float] = Field(None, description="정규화된 스코어")
    composite_score: Optional[float] = Field(None, description="컴포지트 스코어")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()


class PortfolioData(BaseModel):
    """포트폴리오 데이터 모델"""
    ticker: str = Field(..., description="종목 코드")
    weight: float = Field(..., description="비중")
    score: float = Field(..., description="스코어")
    sector: Optional[str] = Field(None, description="섹터")
    country: Optional[str] = Field(None, description="국가")
    constraints_ok: bool = Field(True, description="제약 조건 만족 여부")
    rebalance_date: date = Field(..., description="리밸런스 날짜")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()
    
    @validator('weight')
    def validate_weight(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Weight must be between 0 and 1')
        return v


def validate_dataframe_schema(df: pd.DataFrame, model_class: type) -> pd.DataFrame:
    """DataFrame을 스키마에 맞게 검증하고 정리합니다."""
    if df.empty:
        return df
    
    # 필수 컬럼 확인
    required_fields = []
    for field_name, field_info in model_class.model_fields.items():
        if field_info.is_required():
            required_fields.append(field_name)
    
    missing_columns = [col for col in required_fields if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # 데이터 타입 변환
    for field_name, field_info in model_class.model_fields.items():
        if field_name in df.columns:
            field_type = field_info.annotation
            
            # 날짜 필드 처리
            if field_type == date or field_type == datetime:
                df[field_name] = pd.to_datetime(df[field_name]).dt.date
            
            # 문자열 필드 처리
            elif field_type == str:
                df[field_name] = df[field_name].astype(str)
            
            # 숫자 필드 처리
            elif field_type in [float, int]:
                df[field_name] = pd.to_numeric(df[field_name], errors='coerce')
    
    return df
