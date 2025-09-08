from typing import List, Optional
import pandas as pd
from tabulate import tabulate
from pathlib import Path

REQUIRED_COLUMNS = [
    "ticker","price","shares_outstanding","total_debt","cash_and_equivalents",
    "ebit","ebitda","operating_cash_flow","capital_expenditures"
]

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "ticker" not in df.columns:
        raise ValueError("CSV must include a 'ticker' column.")
    return df

def df_to_markdown(df: pd.DataFrame) -> str:
    return tabulate(df, headers="keys", tablefmt="github", showindex=False)

def save_csv(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
