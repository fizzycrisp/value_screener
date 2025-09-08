from pydantic import BaseModel
from typing import Optional
import yaml

class ScreenConfig(BaseModel):
    ev_ebit_min: float = 5.0
    ev_ebit_max: float = 12.0
    fcf_yield_min: float = 0.07
    roic_min: float = 0.12
    interest_coverage_min: float = 4.0
    net_debt_to_ebitda_max: float = 2.0

def load_config(path: Optional[str]) -> 'ScreenConfig':
    if not path:
        return ScreenConfig()
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return ScreenConfig(**data)
