from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math
import numpy as np
import pandas as pd

@dataclass
class FinancialRow:
    ticker: str
    name: Optional[str]
    price: Optional[float]
    market_cap: Optional[float]
    total_debt: Optional[float]
    cash_and_equivalents: Optional[float]
    ebit: Optional[float]
    ebitda: Optional[float]
    operating_cash_flow: Optional[float]
    capital_expenditures: Optional[float]
    interest_expense: Optional[float] = None
    income_tax_expense: Optional[float] = None
    pretax_income: Optional[float] = None
    total_stockholder_equity: Optional[float] = None
    enterprise_value: Optional[float] = None

def _safe_last(series: pd.Series) -> Optional[float]:
    try:
        val = series.dropna().astype(float)
        return float(val.iloc[0]) if len(val) else None
    except Exception:
        return None

def _prefer_keys(d: Dict[str, Any], keys: List[str]) -> Optional[float]:
    for k in keys:
        if k in d and d[k] is not None and not (isinstance(d[k], float) and math.isnan(d[k])):
            try:
                return float(d[k])
            except Exception:
                continue
    return None

def from_csv_row(row: pd.Series) -> FinancialRow:
    return FinancialRow(
        ticker=row.get("ticker"),
        name=row.get("name"),
        price=row.get("price"),
        market_cap=row.get("price", np.nan) * row.get("shares_outstanding", np.nan) if row.get("market_cap") is None else row.get("market_cap"),
        total_debt=row.get("total_debt"),
        cash_and_equivalents=row.get("cash_and_equivalents"),
        ebit=row.get("ebit"),
        ebitda=row.get("ebitda"),
        operating_cash_flow=row.get("operating_cash_flow"),
        capital_expenditures=row.get("capital_expenditures"),
        interest_expense=row.get("interest_expense"),
        income_tax_expense=row.get("income_tax_expense"),
        pretax_income=row.get("pretax_income"),
        total_stockholder_equity=row.get("total_stockholder_equity"),
        enterprise_value=row.get("enterprise_value"),
    )

def fetch_yfinance(tickers: List[str], timeout: float = 10.0, max_workers: int = 8, max_retries: int = 2, rate_limit_sec: float = 0.0) -> List[FinancialRow]:
    """yfinance를 병렬로 호출하고 티커별 타임아웃/재시도를 적용합니다."""
    import yfinance as yf
    import time
    import concurrent.futures as cf

    def fetch_one(ticker: str) -> FinancialRow:
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                tk = yf.Ticker(ticker)
                info = {}
                try:
                    info.update(getattr(tk, "fast_info", {}) or {})
                except Exception:
                    pass
                try:
                    info.update(getattr(tk, "info", {}) or {})
                except Exception:
                    pass

                price = _prefer_keys(info, ["last_price","lastPrice","regularMarketPrice","currentPrice"])
                mcap = _prefer_keys(info, ["marketCap","market_cap"])

                name = ticker
                for key in ["longName", "shortName", "symbol"]:
                    if key in info and info[key] is not None and isinstance(info[key], str):
                        name = info[key]
                        break

                # Balance Sheet
                bs = None
                for attr in ["get_balance_sheet", "get_balance_sheet", "balance_sheet", "balancesheet"]:
                    try:
                        obj = getattr(tk, attr)()
                        if isinstance(obj, dict) and "yearly" in obj:
                            bs = obj["yearly"]
                        else:
                            bs = obj
                        break
                    except Exception:
                        continue
                total_debt = None
                cash = None
                equity = None
                if bs is not None and hasattr(bs, "index"):
                    def pick(colnames):
                        for cn in colnames:
                            if cn in bs.index:
                                return _safe_last(bs.loc[cn])
                        return None

                    total_debt = pick(["Total Debt","Short Long Term Debt","Short Long-Term Debt","Long Term Debt","Long-Term Debt"])
                    if total_debt is None:
                        lt = pick(["Long Term Debt","Long-Term Debt"])
                        st = pick(["Short Long Term Debt","Short Long-Term Debt"])
                        vals = [v for v in [lt, st] if v is not None]
                        total_debt = float(np.nansum(vals)) if vals else None

                    cash = pick(["Cash And Cash Equivalents","Cash And Cash Equivalents USD","CashAndCashEquivalents"])
                    equity = pick(["Total Stockholder Equity","Total Stockholders Equity","Stockholders Equity"])

                # Income Statement
                inc = None
                for attr in ["get_income_stmt", "get_income_statement", "income_stmt", "income_statement"]:
                    try:
                        obj = getattr(tk, attr)()
                        if isinstance(obj, dict) and "yearly" in obj:
                            inc = obj["yearly"]
                        else:
                            inc = obj
                        break
                    except Exception:
                        continue
                ebit = ebitda = interest_expense = pretax_income = tax_expense = None
                if inc is not None and hasattr(inc, "index"):
                    def pick(colnames):
                        for cn in colnames:
                            if cn in inc.index:
                                return _safe_last(inc.loc[cn])
                        return None
                    ebit = pick(["Ebit","EBIT"])
                    ebitda = pick(["Ebitda","EBITDA"])
                    interest_expense = pick(["Interest Expense","Interest Expense Non Operating"])
                    pretax_income = pick(["Income Before Tax","Pretax Income","Earnings Before Tax"])
                    tax_expense = pick(["Income Tax Expense","Provision for Income Taxes"])

                # Cash Flow
                cf = None
                for attr in ["get_cashflow", "get_cash_flow", "cashflow", "cash_flow"]:
                    try:
                        obj = getattr(tk, attr)()
                        if isinstance(obj, dict) and "yearly" in obj:
                            cf = obj["yearly"]
                        else:
                            cf = obj
                        break
                    except Exception:
                        continue
                ocf = capex = None
                if cf is not None and hasattr(cf, "index"):
                    def pick(colnames):
                        for cn in colnames:
                            if cn in cf.index:
                                return _safe_last(cf.loc[cn])
                        return None
                    ocf = pick(["Total Cash From Operating Activities","Operating Cash Flow"])
                    capex = pick(["Capital Expenditures","Capital Expenditure"])
                    if capex is not None:
                        capex = float(capex)

                # EV
                ev = _prefer_keys(info, ["enterpriseValue","enterprise_value"])
                if ev is None and mcap is not None and total_debt is not None and cash is not None:
                    ev = float(mcap) + float(total_debt) - float(cash)

                return FinancialRow(
                    ticker=ticker,
                    name=str(name) if name else ticker,
                    price=float(price) if price is not None else None,
                    market_cap=float(mcap) if mcap is not None else None,
                    total_debt=float(total_debt) if total_debt is not None else None,
                    cash_and_equivalents=float(cash) if cash is not None else None,
                    ebit=float(ebit) if ebit is not None else None,
                    ebitda=float(ebitda) if ebitda is not None else None,
                    operating_cash_flow=float(ocf) if ocf is not None else None,
                    capital_expenditures=float(capex) if capex is not None else None,
                    interest_expense=float(interest_expense) if interest_expense is not None else None,
                    income_tax_expense=float(tax_expense) if tax_expense is not None else None,
                    pretax_income=float(pretax_income) if pretax_income is not None else None,
                    total_stockholder_equity=float(equity) if equity is not None else None,
                    enterprise_value=float(ev) if ev is not None else None,
                )
            except Exception as e:
                last_exc = e
                if rate_limit_sec > 0:
                    time.sleep(rate_limit_sec)
                continue
        # 실패 시 빈 레코드 반환
        return FinancialRow(ticker=ticker, name=None, price=None, market_cap=None,
                            total_debt=None, cash_and_equivalents=None,
                            ebit=None, ebitda=None, operating_cash_flow=None,
                            capital_expenditures=None)

    rows: List[FinancialRow] = []
    with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_one, t): t for t in tickers}
        for future in cf.as_completed(future_map, timeout=max(1.0, timeout * len(tickers))):
            t = future_map[future]
            try:
                row = future.result(timeout=timeout)
            except Exception:
                row = FinancialRow(ticker=t, name=None, price=None, market_cap=None,
                                   total_debt=None, cash_and_equivalents=None,
                                   ebit=None, ebitda=None, operating_cash_flow=None,
                                   capital_expenditures=None)
            rows.append(row)
    # 순서를 입력 티커 순서로 정렬
    t_index = {t: i for i, t in enumerate(tickers)}
    rows.sort(key=lambda r: t_index.get(r.ticker, 1e9))
    return rows
