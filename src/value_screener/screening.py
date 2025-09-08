from __future__ import annotations
from dataclasses import asdict
from typing import List, Optional, Dict, Any
import math
import pandas as pd
from .metrics import ev_ebit, fcf_yield, roic_approx, net_debt_to_ebitda
from .config import ScreenConfig
from .fetchers import FinancialRow

def build_rows(fin_rows: List[FinancialRow]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for fr in fin_rows:
        rec: Dict[str, Any] = {
            "ticker": fr.ticker,
            "name": fr.name,
            "price": fr.price,
            "market_cap": fr.market_cap,
            "enterprise_value": fr.enterprise_value if fr.enterprise_value is not None else (
                (fr.market_cap or float("nan")) + (fr.total_debt or 0.0) - (fr.cash_and_equivalents or 0.0)
                if fr.market_cap is not None else None
            ),
        }
        # Metrics
        rec["ev_ebit"] = ev_ebit(rec["enterprise_value"], fr.ebit)
        rec["fcf_yield"] = fcf_yield(fr.market_cap, fr.operating_cash_flow, fr.capital_expenditures)
        rec["roic"] = roic_approx(fr.ebit, fr.income_tax_expense, fr.pretax_income,
                                  fr.total_debt, fr.total_stockholder_equity, fr.cash_and_equivalents)
        rec["net_debt_ebitda"] = net_debt_to_ebitda(fr.total_debt, fr.cash_and_equivalents, fr.ebitda)

        records.append(rec)
    df = pd.DataFrame.from_records(records)
    return df

def apply_filters(df: pd.DataFrame, cfg: ScreenConfig) -> pd.DataFrame:
    def in_range(val, lo, hi):
        try:
            return (val >= lo) and (val <= hi)
        except Exception:
            return False
    def ge(val, thresh):
        try:
            return val >= thresh
        except Exception:
            return False
    def lt(val, thresh):
        try:
            return val < thresh
        except Exception:
            return False

    conds = []
    conds.append(df["ev_ebit"].apply(lambda v: in_range(v, cfg.ev_ebit_min, cfg.ev_ebit_max)))
    conds.append(df["fcf_yield"].apply(lambda v: ge(v, cfg.fcf_yield_min)))
    conds.append(df["roic"].apply(lambda v: ge(v, cfg.roic_min)))
    conds.append(df["net_debt_ebitda"].apply(lambda v: lt(v, cfg.net_debt_to_ebitda_max)))

    passed = conds[0]
    for c in conds[1:]:
        passed = passed & c
    df = df.copy()
    df["passed_filters"] = passed
    return df
