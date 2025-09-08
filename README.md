# 밸류 스크리너 (EV/EBIT, FCF 수익률, ROIC)

로컬이나 Docker에서 실행할 수 있는 실용적인 **밸류 주식 스크리너**입니다. 재무 데이터를 가져오고(`yfinance` 사용) 또는 자체 CSV를 읽어서, 품질/밸류에이션 지표를 계산하고 합리적인 기본값을 사용하여 **잠재적으로 저평가된** 종목을 필터링합니다.

> ⚠️ 교육 목적으로만 사용하세요. 투자 조언이 아닙니다. Yahoo Finance의 데이터는 지연되거나 불완전할 수 있습니다.

## 주요 기능
- `yfinance`를 사용하여 데이터를 가져오거나 **또는** CSV에서 읽어옵니다.
- 계산 지표: **EV/EBIT**, **FCF 수익률**, **ROIC (근사치)**, **이자보상배수**, **순부채/EBITDA**.
- 필터 적용 (아래 기본값) 또는 원시 지표 출력:
  - EV/EBIT **5–12** 사이
  - FCF 수익률 **≥ 7%**
  - ROIC **≥ 12%**
  - 이자보상배수 **≥ 4배**
  - 순부채/EBITDA **< 2**
- CSV/마크다운 출력.

## 빠른 시작 (Docker)
```bash
# 1) 빌드
docker build -t value-screener:latest .

# 2) 샘플 한국 종목으로 실행
docker run --rm -v "$PWD:/work" -w /work value-screener:latest   --source yfinance   --tickers 005930.KS 000660.KS 035420.KS   --output results.csv

# 콘솔에서 마크다운 테이블로 표시
docker run --rm value-screener:latest   --source yfinance   --tickers AAPL MSFT GOOGL   --md
```

## 로컬 설치 (Docker 없이)
```bash
# 이 저장소 루트에서
pip install -e .
value-screener --help
```

## 사용법
```bash
value-screener --source {yfinance|csv} [OPTIONS]

옵션:
  --tickers TEXT...            종목 코드 (공백으로 구분). 예: AAPL MSFT
  --file PATH                  --source=csv일 때, CSV 파일 경로.
  --config PATH                임계값을 위한 YAML 설정 (sample/config.yaml 참조).
  --no-filter                  지표만 출력하고 필터링하지 않음.
  --output PATH                콘솔 외에 결과를 CSV로 저장.
  --md                         일반 텍스트 대신 마크다운 테이블로 출력.
  --timeout FLOAT              종목당 타임아웃 (초) (yfinance).
  --max-workers INTEGER        병렬 가져오기 풀 크기 (기본값: 8).
  -q, --quiet                  로그 줄이기.
  --help                       이 메시지 표시.
```

### CSV 스키마 (`--source=csv` 사용 시)
최소한 다음 컬럼들을 제공하세요 (TTM 또는 최근 연간):
- `ticker`, `price`, `shares_outstanding`, `total_debt`, `cash_and_equivalents`, `ebit`, `ebitda`, `operating_cash_flow`, `capital_expenditures`
- 추가 지표를 위한 선택사항: `income_tax_expense`, `pretax_income`, `total_stockholder_equity`

추가 필드를 포함할 수 있지만 무시됩니다.

헤더는 [`sample/financials_schema.csv`](sample/financials_schema.csv)를 참조하세요.

## 설정 (임계값)
[`sample/config.yaml`](sample/config.yaml)을 참조하세요. 제공되지 않으면 기본값이 사용됩니다.

## 출력
컬럼 포함:
- `ticker`, `name`, `price`, `market_cap`, `enterprise_value`,
- `ev_ebit`, `fcf_yield`, `roic`, `interest_coverage`, `net_debt_ebitda`,
- `passed_filters` (True/False)

CSV를 저장하려면 `--output results.csv`를 사용하세요. 마크다운으로 출력하려면 `--md`를 추가하세요.

## 제한사항
- 일부 종목은 Yahoo에서 필드가 누락될 수 있습니다. 도구는 `nan`으로 표시하고 `--no-filter`를 사용하지 않는 한 필터를 건너뜁니다.
- ROIC는 근사치입니다: `NOPAT / InvestedCapital`에서 `NOPAT ≈ EBIT*(1-taxRate)`이고 `InvestedCapital ≈ TotalDebt + Equity - Cash`입니다 (CODE_GUIDE.md 참조).

## 예제
```bash
# 미국 대형주 스크리닝
value-screener --source yfinance --tickers AAPL MSFT GOOGL NVDA --md

# 한국 종목의 지표만 계산, 필터 없음
value-screener --source yfinance --tickers 005930.KS 000660.KS --no-filter --md

# CSV와 사용자 정의 설정 사용
value-screener --source csv --file my_financials.csv --config my_config.yaml --output picked.csv
```
