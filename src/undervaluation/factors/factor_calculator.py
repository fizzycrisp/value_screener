"""
팩터 계산기
BMad 협업으로 구현된 통합 팩터 계산 시스템
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

from .value_factors import (
    calculate_earnings_yield,
    calculate_fcf_yield,
    calculate_book_to_market
)
from .quality_factors import (
    calculate_gross_profitability,
    calculate_roic,
    calculate_interest_coverage
)


class FactorCalculator:
    """통합 팩터 계산기"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 가중치 설정
        self.weights = config.get('weights', {})
        
    def calculate_all_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """모든 팩터를 계산합니다."""
        self.logger.info("Calculating all factors...")
        
        result_df = df.copy()
        
        # 밸류 팩터
        result_df = self._calculate_value_factors(result_df)
        
        # 퀄리티 팩터
        result_df = self._calculate_quality_factors(result_df)
        
        # 회계 품질 팩터 (간단한 버전)
        result_df = self._calculate_accounting_factors(result_df)
        
        # 투자/발행 팩터 (간단한 버전)
        result_df = self._calculate_investment_factors(result_df)
        
        # 모멘텀 팩터 (간단한 버전)
        result_df = self._calculate_momentum_factors(result_df)
        
        # 컴포지트 스코어 계산
        result_df = self._calculate_composite_score(result_df)
        
        self.logger.info(f"Factor calculation completed for {len(result_df)} stocks")
        return result_df
    
    def _calculate_value_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """밸류 팩터를 계산합니다."""
        self.logger.debug("Calculating value factors...")
        
        # Earnings Yield
        if all(col in df.columns for col in ['ebit', 'enterprise_value']):
            df['earnings_yield'] = calculate_earnings_yield(
                df['ebit'], df['enterprise_value']
            )
        
        # FCF Yield
        if all(col in df.columns for col in ['operating_cash_flow', 'capital_expenditures', 'market_cap']):
            df['fcf_yield'] = calculate_fcf_yield(
                df['operating_cash_flow'], 
                df['capital_expenditures'], 
                df['market_cap']
            )
        
        # Book-to-Market
        if all(col in df.columns for col in ['total_equity', 'market_cap']):
            df['book_to_market'] = calculate_book_to_market(
                df['total_equity'], df['market_cap']
            )
        
        return df
    
    def _calculate_quality_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """퀄리티 팩터를 계산합니다."""
        self.logger.debug("Calculating quality factors...")
        
        # Gross Profitability
        if all(col in df.columns for col in ['gross_profit', 'total_assets']):
            df['gross_profitability'] = calculate_gross_profitability(
                df['gross_profit'], df['total_assets']
            )
        
        # ROIC
        if all(col in df.columns for col in ['ebit', 'income_tax_expense', 'pretax_income', 
                                           'total_debt', 'total_equity', 'cash_and_equivalents']):
            df['roic'] = calculate_roic(
                df['ebit'],
                df['income_tax_expense'],
                df['pretax_income'],
                df['total_debt'],
                df['total_equity'],
                df['cash_and_equivalents']
            )
        
        # Interest Coverage
        if all(col in df.columns for col in ['ebit', 'interest_expense']):
            df['interest_coverage'] = calculate_interest_coverage(
                df['ebit'], df['interest_expense']
            )
        
        return df
    
    def _calculate_accounting_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """회계 품질 팩터를 계산합니다."""
        self.logger.debug("Calculating accounting factors...")
        
        # 간단한 발생액률 계산 (순이익 - 영업현금흐름) / 총자산
        if all(col in df.columns for col in ['operating_cash_flow', 'total_assets']):
            # 순이익이 없으면 EBIT로 근사
            if 'net_income' in df.columns:
                net_income = df['net_income']
            else:
                net_income = df.get('ebit', 0)
            
            df['accruals'] = (net_income - df['operating_cash_flow']) / df['total_assets']
        
        # NOA/Assets (간단한 버전)
        if all(col in df.columns for col in ['total_assets', 'cash_and_equivalents']):
            # NOA = Total Assets - Cash (간단한 근사)
            noa = df['total_assets'] - df['cash_and_equivalents']
            df['noa_ratio'] = noa / df['total_assets']
        
        # Risk Flags (간단한 버전)
        df['risk_flags'] = 0
        if 'interest_coverage' in df.columns:
            df.loc[df['interest_coverage'] < 2.5, 'risk_flags'] += 1
        if 'total_debt' in df.columns and 'total_equity' in df.columns:
            debt_equity = df['total_debt'] / df['total_equity']
            df.loc[debt_equity > 1, 'risk_flags'] += 1
        
        return df
    
    def _calculate_investment_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """투자/발행 팩터를 계산합니다."""
        self.logger.debug("Calculating investment factors...")
        
        # Asset Growth (간단한 버전 - 현재는 0으로 설정)
        df['asset_growth'] = 0
        
        # Net Issuance (간단한 버전 - 현재는 0으로 설정)
        df['net_issuance'] = 0
        
        return df
    
    def _calculate_momentum_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """모멘텀 팩터를 계산합니다."""
        self.logger.debug("Calculating momentum factors...")
        
        # Momentum 12-1 (간단한 버전 - 현재는 0으로 설정)
        df['momentum_12m_1m'] = 0
        
        return df
    
    def _calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """컴포지트 스코어를 계산합니다."""
        self.logger.debug("Calculating composite score...")
        
        # 가중치 설정
        weights = self.weights
        
        # 각 팩터별 점수 계산 (z-score 기반)
        factor_columns = [
            'earnings_yield', 'fcf_yield', 'book_to_market',
            'gross_profitability', 'roic',
            'accruals', 'noa_ratio', 'risk_flags',
            'asset_growth', 'net_issuance',
            'momentum_12m_1m'
        ]
        
        # 정규화된 팩터 점수 계산
        for col in factor_columns:
            if col in df.columns:
                # z-score 계산
                mean_val = df[col].mean()
                std_val = df[col].std()
                
                if std_val > 0:
                    df[f'{col}_normalized'] = (df[col] - mean_val) / std_val
                else:
                    df[f'{col}_normalized'] = 0
        
        # 컴포지트 스코어 계산
        composite_score = pd.Series(0, index=df.index)
        
        # 밸류 팩터 (40%)
        value_weight = weights.get('value', {})
        if 'earnings_yield' in df.columns and 'earnings_yield_normalized' in df.columns:
            composite_score += df['earnings_yield_normalized'] * value_weight.get('ey', 0.20)
        if 'fcf_yield' in df.columns and 'fcf_yield_normalized' in df.columns:
            composite_score += df['fcf_yield_normalized'] * value_weight.get('fcfy', 0.10)
        if 'book_to_market' in df.columns and 'book_to_market_normalized' in df.columns:
            composite_score += df['book_to_market_normalized'] * value_weight.get('bm', 0.10)
        
        # 퀄리티 팩터 (30%)
        quality_weight = weights.get('quality', {})
        if 'gross_profitability' in df.columns and 'gross_profitability_normalized' in df.columns:
            composite_score += df['gross_profitability_normalized'] * quality_weight.get('gross_prof', 0.15)
        if 'roic' in df.columns and 'roic_normalized' in df.columns:
            composite_score += df['roic_normalized'] * quality_weight.get('roic', 0.10)
        
        # 회계 품질 팩터 (15%) - 낮을수록 좋으므로 부호 반전
        accounting_weight = weights.get('accounting', {})
        if 'accruals' in df.columns and 'accruals_normalized' in df.columns:
            composite_score -= df['accruals_normalized'] * abs(accounting_weight.get('accruals', 0.07))
        if 'noa_ratio' in df.columns and 'noa_ratio_normalized' in df.columns:
            composite_score -= df['noa_ratio_normalized'] * abs(accounting_weight.get('noa', 0.05))
        if 'risk_flags' in df.columns and 'risk_flags_normalized' in df.columns:
            composite_score -= df['risk_flags_normalized'] * abs(accounting_weight.get('risk', 0.03))
        
        # 투자/발행 팩터 (10%) - 낮을수록 좋으므로 부호 반전
        investment_weight = weights.get('investment', {})
        if 'asset_growth' in df.columns and 'asset_growth_normalized' in df.columns:
            composite_score -= df['asset_growth_normalized'] * abs(investment_weight.get('asset_growth', 0.05))
        if 'net_issuance' in df.columns and 'net_issuance_normalized' in df.columns:
            composite_score -= df['net_issuance_normalized'] * abs(investment_weight.get('net_issuance', 0.05))
        
        # 모멘텀 팩터 (5%)
        momentum_weight = weights.get('momentum', {})
        if 'momentum_12m_1m' in df.columns and 'momentum_12m_1m_normalized' in df.columns:
            composite_score += df['momentum_12m_1m_normalized'] * momentum_weight.get('m12m_1m', 0.05)
        
        # 스코어 클리핑 (±3σ)
        score_std = composite_score.std()
        if score_std > 0:
            composite_score = composite_score.clip(-3 * score_std, 3 * score_std)
        
        df['composite_score'] = composite_score
        
        return df
