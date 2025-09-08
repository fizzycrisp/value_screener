from __future__ import annotations
from typing import Optional, Dict, Any
import math

def ev_ebit(ev: Optional[float], ebit: Optional[float]) -> Optional[float]:
    if ev is None or ebit is None:
        return None
    if ebit == 0:
        return None
    return ev / ebit

def fcf_yield(market_cap: Optional[float], ocf: Optional[float], capex: Optional[float]) -> Optional[float]:
    if market_cap is None or market_cap == 0 or ocf is None or capex is None:
        return None
    fcf = ocf - capex  # capex usually negative => subtracting adds magnitude
    return fcf / market_cap

def roic_approx(ebit: Optional[float],
                tax_expense: Optional[float],
                pretax_income: Optional[float],
                total_debt: Optional[float],
                equity: Optional[float],
                cash: Optional[float]) -> Optional[float]:
    if ebit is None or total_debt is None or equity is None or cash is None:
        return None
    # Estimate tax rate
    tax_rate = 0.25
    try:
        if pretax_income is not None and pretax_income != 0 and tax_expense is not None:
            tr = tax_expense / pretax_income
            if math.isfinite(tr):
                tax_rate = max(0.0, min(0.45, tr))
    except Exception:
        pass
    nopat = ebit * (1 - tax_rate)
    invested_capital = total_debt + equity - cash
    if invested_capital <= 0:
        return None
    return nopat / invested_capital

def interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    if ebit is None or interest_expense is None:
        return None
    ie = abs(interest_expense)
    if ie == 0:
        return None
    return ebit / ie

def net_debt_to_ebitda(total_debt: Optional[float], cash: Optional[float], ebitda: Optional[float]) -> Optional[float]:
    if total_debt is None or cash is None or ebitda is None or ebitda == 0:
        return None
    net_debt = total_debt - cash
    return net_debt / ebitda
