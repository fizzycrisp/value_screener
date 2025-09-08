# 저평가 주식 스크리닝 알고리즘 — 구현 작업 지침서 (for 코드 에이전트)

> 목표: \*\*“싸고(Valuation), 좋고(Quality), 속이지 않으며(Accounting Quality), 과잉투자/희석 위험이 낮고(Investment/Issuance), 지금 무너지지 않는 종목(Momentum)”\*\*을 **섹터‑중립**으로 선별하는 엔진을 구현한다.

---

## 0. 결과물 개요 (Done 기준)

* **라이브러리/CLI**/Docker 실행 가능.
* 입력: 데이터 소스(yfinance/CSV/타 API), 티커 리스트, 설정(YAML).
* 출력:

  1. 종목별 지표 테이블(CSV/MD),
  2. 컴포지트 스코어·랭킹,
  3. 후보 포트폴리오(제약 반영),
  4. 백테스트 리포트(성과·리스크·턴오버).
* **재현성**: 보고지연(래깅), 슬리피지, 거래비용 모델 포함.
* 테스트: 유닛/통합/회귀 테스트 통과.

---

## 1. 프로젝트 스켈레톤 생성

**해야 할 일**

1. 패키지 레이아웃:

   ```
   src/undervaluation/
     data/         # 커넥터 & 캐시
     schemas/      # 유니파이드 스키마 정의
     factors/      # 지표 산출식
     ranking/      # 정규화/섹터중립/컴포지트
     screens/      # 게이트·제외 규칙
     portfolio/    # 구성/제약/리밸런스
     backtest/     # 시뮬레이터
     utils/        # 공통(통화/날짜/로그)
     cli.py        # 엔트리포인트
   configs/
     default.yaml
   tests/
   ```
2. **pyproject.toml**: pandas, numpy, pydantic, click, PyYAML, scipy(정규화·winsorize), statsmodels(선택), tabulate, tqdm.
3. **Dockerfile**: `python:3.11-slim` 기반, `pip install .`; ENTRYPOINT `uv-screen`(예: 콘솔 스크립트).

**수용 기준**

* `uv-screen --help` 동작.
* 기본 Docker 이미지 빌드·실행 성공.

---

## 2. 데이터 소스 커넥터(플러그인형)

**해야 할 일**

1. 인터페이스 정의(추상화):

   ```python
   class DataSource(Protocol):
       def fetch_universe(self, tickers: list[str], asof: date) -> pd.DataFrame: ...
       def fetch_fundamentals(self, tickers: list[str], asof: date) -> pd.DataFrame: ...
       def fetch_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame: ...
   ```
2. **yfinanceConnector**(기본): 가격·시총·간단 재무.
3. **CSVConnector**: 내부 CSV 스키마(§3) 준수 시 그대로 로드.
4. 확장 포인트(스텁만): `FMPConnector`, `EODHDConnector`, `DARTConnector`. (키는 환경변수로 주입: `FMP_API_KEY`, `EODHD_TOKEN`, `DART_API_KEY`)

**수용 기준**

* 커넥터가 **유니파이드 스키마**(§3)로 변환된 DF 반환.
* 미존재 필드 `NaN` 처리·로그 경고.
* 타임아웃/재시도/레이트리밋 기본기 탑재.

---

## 3. 유니파이드 데이터 스키마

**필수 필드(열)**

```
ticker, currency, price, market_cap, enterprise_value,
total_debt, cash_and_equivalents, total_equity,
ebit, ebitda, gross_profit,
operating_cash_flow, capital_expenditures,
pretax_income, income_tax_expense, interest_expense,
total_assets, shares_outstanding, reporting_date
```

**권장 필드**

```
sector, industry, country, filing_date, restatement_flag,
share_issuance(net), buyback(net), asset_growth, noa
```

**해야 할 일**

* 통화 일관화(기본 통화 = USD 또는 KRW, `fx_table`로 환산).
* 회계기간 정합성: TTM 우선, 없으면 최근 연간.
* `enterprise_value` 없으면 `EV = market_cap + total_debt - cash`.
* `noa = (operating_assets - operating_liabilities)` 근사치도 계산 가능(§6C).

**수용 기준**

* 스키마 밸리데이션(pydantic Model).
* 통화·기간 치환이 로깅되며 재현 가능.

---

## 4. 핵심 팩터 계산 모듈

**공식(방향: 높을수록 우수)**

* **EY (Earnings Yield)**: $\text{EY} = \frac{\text{EBIT}}{\text{EV}}$
* **FCF Yield**: $\frac{\text{OCF} - \text{CapEx}}{\text{MarketCap}}$
* **B/M**: $\frac{\text{TotalEquity}}{\text{MarketCap}}$
* **Gross Profitability**: $\frac{\text{GrossProfit}}{\text{TotalAssets}}$
* **ROIC(근사)**:

  * $\text{TaxRate} \approx \mathrm{clip}\left( \frac{\text{Tax}}{\text{Pretax}}, 0, 0.45 \right)$ (fallback 25%)
  * $\text{NOPAT} = \text{EBIT}\times(1-\text{TaxRate})$
  * $\text{InvestedCapital} \approx \text{TotalDebt} + \text{TotalEquity} - \text{Cash}$
  * $\text{ROIC} = \frac{\text{NOPAT}}{\text{InvestedCapital}}$
* **Net Debt / EBITDA**: $\frac{\text{TotalDebt}-\text{Cash}}{\text{EBITDA}}$ (낮을수록 우수)
* **Accruals/Assets(총 발생액률)**: $\frac{\Delta \text{NWC} + \Delta \text{NCA} - \Delta \text{Cash} - \text{Dep}}{\text{TotalAssets}}$ (낮을수록 우수)
  *(간략화 가능: $(\text{NI} - \text{CFO}) / \text{Assets})$*
* **NOA/Assets**: $\frac{\text{NOA}}{\text{Assets}}$ (낮을수록 우수)
* **Beneish M-Score**, **Altman Z-Score**: 표준식 구현(게이트용).
* **Momentum(12-1)**: 월별 리턴 기반 누적(최근 12개월 – 최근 1개월).

**해야 할 일**

* 결측·0분모 방지(가드).
* 입력 라벨 표준화(다른 소스 키 매핑).
* 팩터 유닛 테스트(샘플 벡터 대비 기대치).

**수용 기준**

* 각 함수에 docstring(공식·단위), 유닛 테스트 90%+ 커버리지.

---

## 5. 정규화·섹터중립·이상치 처리

**해야 할 일**

1. **섹터×시가총액 버킷**(예: 섹터 11개 × Small/Mid/Large 3구간)으로 그룹핑.
2. 각 팩터를 그룹 내 **랭크 → z-스코어** 변환.
3. **윈저라이즈**(상·하위 1% 클리핑), 스케일 표준화.
4. 방향 통일(높을수록 좋도록 부호 전환).
5. 결측치: 그룹 중앙값으로 대체 + 패널티(예: z‑0.2).

**수용 기준**

* 그룹별 평균 0, 표준편차 1에 근접.
* 결측치 비율·대체 로깅.

---

## 6. 게이트 규칙(배제/경고)

**해야 할 일**

* **필수 배제**:

  * Beneish M > 임계, Altman Z < 임계, 감사의견 부적정/한정, 빈번한 정정공시, 거래정지.
* **리스크 플래그**(경고):

  * 고발행(순발행>0 임계), 고자산성장, 급격한 마진붕괴, 유동성 부족(거래대금·스프레드).

**수용 기준**

* 게이트 통과 여부 컬럼(`gate_passed: bool`), 사유 컬럼(`gate_reason`).

---

## 7. 컴포지트 스코어

**권장 가중치(기본값, 설정파일에서 조정 가능)**

* `Value 40%` = EY 20 + FCFY 10 + B/M 10
* `Quality 30%` = GrossProf 15 + ROIC 10 + (보조)F‑Score 5
* `Accounting/Risk 15%` = (–Accruals) 7 + (–NOA) 5 + (–RiskFlags) 3
* `Investment/Issuance 10%` = (–AssetGrowth) 5 + (–NetIssuance) 5
* `Momentum 5%` = 12‑1

**해야 할 일**

* 컴포지트 = 가중합(z-스코어), 상·하한 클리핑(±3σ).
* **밴딩**: 상위 밴드±ε(예: 0.25σ) 유지 시 보유 지속 → 턴오버 억제.

**수용 기준**

* 스코어 분포·상관행렬 리포트 생성.
* 설정 변경 시 재계산·결과 동일성(같은 랜덤시드) 보장.

---

## 8. 스크리닝 & 포트폴리오 구성

**해야 할 일**

1. **유동성 게이트**: 시총/평균거래대금/스프레드 컷인.
2. **랭킹 선택**: 스코어 상위 K(예: 상위 20\~30%) → 후보군.
3. **제약 최적화(선택)**: 섹터 상한(예 20%), 단일 종목 상한(예 7%), 국가/통화 노출 관리.

   * 단순 규칙(휴리스틱) 또는 경량 QP(제약 충족 최대합 스코어).
4. **리밸런스**: 분기 1회(월별 분산 추천), 밴딩·거래비용 반영.

**수용 기준**

* 결과 포트폴리오 CSV: `ticker, weight, score, sector, constraints_ok`.
* 제약 위반 0건.

---

## 9. 백테스트 엔진

**해야 할 일**

1. **캘린더**: 리밸런스 스케줄(월/분기), 실행일 D+1 체결.
2. **보고지연(래깅)**: 재무 데이터 **공시일 + X일** 이후만 사용.
3. **거래비용 모델**: 고정bps + 스프레드 기반 슬리피지(단순).
4. **성과 지표**: 누적수익, 연환산수익/변동성, 샤프, 최대낙폭, 승률, 턴오버, 드로다운 기간.
5. **벤치마크 비교**: 시장/밸류·퀄리티 팩터 인덱스 대비 초과수익.

**수용 기준**

* 리포트(표·그래프) 생성: 성과, 위험, 요인 노출(간단 회귀).
* 시드 고정 시 결과 재현.

---

## 10. 설정(컨피그) & CLI

**config 예시(`configs/default.yaml`)**

```yaml
universe:
  min_market_cap: 5e8          # 최소 시총
  min_adv_usd: 2e6             # 일평균 거래대금(USD 환산)
  country_whitelist: [KR, US]

normalization:
  winsorize_pct: 0.01
  group_by: ["sector", "size_bucket"]

weights:
  value: {ey: 0.20, fcfy: 0.10, bm: 0.10}
  quality: {gross_prof: 0.15, roic: 0.10, fscore: 0.05}
  accounting: {accruals: -0.07, noa: -0.05, risk: -0.03}
  investment: {asset_growth: -0.05, net_issuance: -0.05}
  momentum: {m12m_1m: 0.05}

gates:
  beneish_max: -1.78
  altman_min: 1.8
  allow_restatement: false

portfolio:
  top_pct: 0.25
  max_weight_per_name: 0.07
  max_weight_per_sector: 0.20
  rebalance: "quarterly"
  band_sigma: 0.25
  tc_bps: 20

backtest:
  start: "2018-01-01"
  end: "2025-08-31"
  report_lag_days: 45
```

**CLI 예시**

```bash
uv-screen screen \
  --source yfinance --tickers AAPL MSFT GOOGL 005930.KS \
  --config configs/default.yaml --output out/screen.csv --md

uv-screen backtest \
  --source csv --file data/universe_krus.csv \
  --config configs/default.yaml --report out/
```

**수용 기준**

* 설정파일로 모든 임계·가중·제약 조정 가능.
* 잘못된 설정 값에 대한 명확한 오류 메시지.

---

## 11. 데이터 품질 & 예외 처리

**해야 할 일**

* 단위/부호 통일(CapEx 대개 음수 → 사용 시 일관).
* `EBITDA==0` 등 분모 문제 → `NaN` + 경고.
* 이상치 탐지 로그(전기 대비 ±200% 급변).
* 엔티티 매핑: KR 티커(6자리+거래소 suffix) 정규화, 시세/재무 병합 키 확정.

**수용 기준**

* 품질 리포트: 결측률/이상치 카운트/교정 내역.

---

## 12. 리포팅

**해야 할 일**

* 스크리닝 결과 **Markdown 표** + CSV 출력.
* 백테스트 요약(연수익/샤프/MDD/턴오버) 표 + 드로다운 곡선.
* 팩터 기여도(간단)·섹터/시가총액 분해.

**수용 기준**

* `out/` 폴더에 일괄 저장, 파일명에 타임스탬프 포함.

---

## 13. 테스트 전략

**유닛 테스트**

* 팩터 공식(입력→기대 출력).
* 정규화/윈저라이즈/밴딩 경계값.

**통합 테스트**

* 소형 샘플(10개 티커)로 end‑to‑end 스크린/백테스트.

**회귀 테스트**

* 고정 시드·버전에서 결과 요약 통계(±허용오차) 불변.

**수용 기준**

* CI에서 모든 테스트 GREEN.

---

## 14. 성능·캐싱·재현성

**해야 할 일**

* 가격/재무 요청 **디스크 캐시**(키: 소스+티커+asof).
* 병렬 처리(티커단 futures)·진행바.
* 난수 시드 고정(포트폴리오 타이브레이커 등).

**수용 기준**

* 동일 입력·시드 → 동일 결과.

---

## 15. 보안/라이선스/컴플라이언스

**해야 할 일**

* API 키는 환경변수만 허용(.env 파일 제외).
* 외부 데이터 사용 약관 링크를 README에 명시.
* 로깅에 민감정보 마스킹.

---

## 16. 문서화

**해야 할 일**

* `README.md`: 설치/실행/예시/제약.
* `docs/ALGORITHM.md`: 본 문서(설계·공식·흐름도·한계).
* `docs/DATA_SOURCES.md`: 커넥터별 필드 매핑 표.

---

## 부록 A. 팩터 계산 의사코드

```text
for each ASOF_DATE:
  DF = load_unified_fundamentals(ASOF_DATE - report_lag)
  PX = load_prices(window=[ASOF_DATE-13M, ASOF_DATE])
  FEAT = compute_factors(DF, PX)           # §4
  FEAT_NORM = normalize_by_group(FEAT)     # §5
  GATE = apply_gates(FEAT, DF)             # §6
  SCORE = composite(FEAT_NORM, weights)    # §7
  CAND = filter_by_liquidity_and_gates(SCORE, GATE)
  PORT = construct_portfolio(CAND, constraints)  # §8
  if BACKTEST:
     simulate_trades(prev_port, PORT, costs)     # §9
     record_metrics()
```

---

## 부록 B. 최소 CSV 스키마(헤더)

```
ticker,currency,price,market_cap,enterprise_value,total_debt,cash_and_equivalents,
total_equity,ebit,ebitda,gross_profit,operating_cash_flow,capital_expenditures,
pretax_income,income_tax_expense,interest_expense,total_assets,shares_outstanding,
sector,industry,country,reporting_date,filing_date
```

---

### 체크리스트 (요약)

* [ ] 커넥터(yf/CSV) → 유니파이드 스키마 매핑
* [ ] 팩터 계산(공식·가드) + 유닛 테스트
* [ ] 섹터×규모 정규화 + 윈저라이즈
* [ ] 게이트(Beneish/Altman/공시 이벤트)
* [ ] 컴포지트 가중·밴딩
* [ ] 포트폴리오 제약·리밸런스
* [ ] 백테스트(래깅/비용/슬리피지)
* [ ] CLI/Docker/설정파일
* [ ] 리포트(표·그래프)
* [ ] 품질·성능·보안·문서·CI

---

**주의**: 본 설계는 리서치/교육 목적입니다. 실제 투자 판단과 책임은 사용자에게 있으며, 데이터 소스의 정확도·지연·이용약관을 반드시 확인하십시오.
