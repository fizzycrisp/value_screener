# 코드 가이드: 아키텍처 및 방법론

이 문서는 스크리너가 각 지표를 **어떻게** 계산하고 데이터가 어디서 오는지 설명합니다.

## 구조
```
src/value_screener/
  ├── cli.py           # CLI 진입점 (Click)
  ├── config.py        # Pydantic 모델 + YAML 로더
  ├── io.py            # CSV IO, 마크다운/CSV 렌더링
  ├── fetchers.py      # yfinance / CSV 로더
  ├── metrics.py       # 재무 지표 계산
  └── screening.py     # 지표 + 임계값을 조율하는 필터 로직
```
`value-screener` 콘솔 명령은 `value_screener.cli:main`에 매핑됩니다.

## 데이터 소스
- **yfinance**: *빠른* 필드(가격/시가총액)와 *전체* 재무제표를 혼합하여 가져옵니다:
  - 가격/이름/시가총액: `Ticker.fast_info`, `Ticker.info`
  - 손익계산서: `Ticker.get_income_stmt()` 또는 `Ticker.income_stmt`
  - 대차대조표: `Ticker.get_balance_sheet()` 또는 `Ticker.balance_sheet`
  - 현금흐름표: `Ticker.get_cashflow()` 또는 `Ticker.cashflow`
- **CSV**: 필요한 필드를 직접 제공할 수 있습니다.

> 로더는 yfinance 버전 간의 견고성을 위해 **여러 속성 이름**을 시도합니다.

## 지표 공식

### 기업가치 (EV)
```
EV = MarketCap + TotalDebt - CashAndEquivalents
```
Yahoo에서 `enterpriseValue`를 제공하면 이를 우선 사용합니다.

### EV/EBIT
```
EV_EBIT = EV / EBIT
```
EBIT는 가능한 경우 12개월 추적(TTM)을 사용하고, 그렇지 않으면 최근 연간 기간을 사용합니다.

### FCF 수익률
```
FCF = OperatingCashFlow - CapitalExpenditures
FCF_Yield = FCF / MarketCap
```

### ROIC (근사치)
```
TaxRate ≈ IncomeTaxExpense / PretaxIncome   (0–45%로 제한, 기본값 25%)
NOPAT   ≈ EBIT * (1 - TaxRate)
InvestedCapital ≈ TotalDebt + TotalEquity - CashAndEquivalents
ROIC   ≈ NOPAT / InvestedCapital
```

### 이자보상배수
```
InterestCoverage = EBIT / |InterestExpense|
```

### 순부채 / EBITDA
```
NetDebt = TotalDebt - CashAndEquivalents
NetDebtToEBITDA = NetDebt / EBITDA
```

## 필터 (기본값)
- `ev_ebit_min = 5`, `ev_ebit_max = 12`
- `fcf_yield_min = 0.07`
- `roic_min = 0.12`
- `interest_coverage_min = 4`
- `net_debt_to_ebitda_max = 2`

`--config`를 통해 재정의할 수 있습니다.

## 확장
- `screening.py`에서 섹터별 스크린을 추가하세요 (예: 소프트웨어의 40 규칙).
- 동일한 재무제표를 사용하여 `metrics.py`에서 피오트로스키 F-스코어를 구현하세요.
