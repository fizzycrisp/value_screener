# Value Screener 아키텍처 개선 로드맵

## 🎯 Phase 1: 핵심 아키텍처 개선 (1-2주)

### 1.1 레이어드 아키텍처 도입
```
src/value_screener/
├── presentation/          # CLI, API 인터페이스
│   ├── cli.py
│   ├── api.py            # FastAPI 기반 REST API
│   └── web/              # 웹 UI (Streamlit/Dash)
├── business/             # 비즈니스 로직
│   ├── screening/
│   │   ├── strategies/   # 다양한 스크리닝 전략
│   │   └── filters.py
│   ├── metrics/
│   │   ├── calculators/  # 지표 계산기
│   │   └── plugins/      # 플러그인 시스템
│   └── analysis/
│       └── reporting.py
├── data/                 # 데이터 접근 계층
│   ├── repositories/
│   ├── fetchers/
│   └── models/
└── infrastructure/       # 인프라 계층
    ├── config/
    ├── logging/
    ├── caching/
    └── monitoring/
```

### 1.2 의존성 주입 컨테이너
- `dependency-injector` 라이브러리 도입
- 설정, 로거, 데이터 소스 주입 가능하게 구성

### 1.3 인터페이스 정의
```python
# data/interfaces.py
class DataFetcher(ABC):
    @abstractmethod
    async def fetch_ticker_data(self, ticker: str) -> FinancialData:
        pass

class MetricCalculator(ABC):
    @abstractmethod
    def calculate(self, data: FinancialData) -> Dict[str, float]:
        pass

class ScreeningStrategy(ABC):
    @abstractmethod
    def apply(self, df: pd.DataFrame, config: ScreenConfig) -> pd.DataFrame:
        pass
```

## 🚀 Phase 2: 확장성 및 성능 (2-3주)

### 2.1 플러그인 시스템
```python
# metrics/plugins/base.py
class MetricPlugin(ABC):
    @abstractmethod
    def calculate(self, data: FinancialData) -> Optional[float]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass

# 새로운 지표 추가 예시
class PiotroskiFScore(MetricPlugin):
    def calculate(self, data: FinancialData) -> Optional[float]:
        # 피오트로스키 F-스코어 계산 로직
        pass
```

### 2.2 전략 패턴 구현
```python
# screening/strategies/
class ValueStrategy(ScreeningStrategy):
    def apply(self, df: pd.DataFrame, config: ScreenConfig) -> pd.DataFrame:
        # 밸류 투자 전략 필터링
        pass

class GrowthStrategy(ScreeningStrategy):
    def apply(self, df: pd.DataFrame, config: ScreenConfig) -> pd.DataFrame:
        # 성장주 투자 전략 필터링
        pass

class QualityStrategy(ScreeningStrategy):
    def apply(self, df: pd.DataFrame, config: ScreenConfig) -> pd.DataFrame:
        # 품질주 투자 전략 필터링
        pass
```

### 2.3 비동기 처리 도입
```python
# data/fetchers/async_fetcher.py
import asyncio
import aiohttp

class AsyncYFinanceFetcher(DataFetcher):
    async def fetch_multiple_tickers(self, tickers: List[str]) -> List[FinancialData]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_ticker_data(ticker, session) for ticker in tickers]
            return await asyncio.gather(*tasks, return_exceptions=True)
```

### 2.4 캐싱 레이어
```python
# infrastructure/caching/
class CacheManager:
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    async def get_or_fetch(self, key: str, fetcher: Callable) -> Any:
        cached = await self.backend.get(key)
        if cached:
            return cached
        
        data = await fetcher()
        await self.backend.set(key, data, ttl=3600)  # 1시간 TTL
        return data
```

## 📊 Phase 3: 모니터링 및 운영 (1-2주)

### 3.1 구조화된 로깅
```python
# infrastructure/logging/
import structlog

logger = structlog.get_logger()

# 사용 예시
logger.info("screening_started", 
           tickers=len(tickers), 
           strategy="value",
           user_id=user_id)
```

### 3.2 메트릭 수집
```python
# infrastructure/monitoring/
class MetricsCollector:
    def __init__(self):
        self.counters = {}
        self.timers = {}
    
    def increment_counter(self, name: str, value: int = 1):
        self.counters[name] = self.counters.get(name, 0) + value
    
    def record_timing(self, name: str, duration: float):
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(duration)
```

### 3.3 헬스체크 및 상태 모니터링
```python
# infrastructure/health/
class HealthChecker:
    async def check_data_sources(self) -> Dict[str, bool]:
        return {
            "yfinance": await self._check_yfinance(),
            "database": await self._check_database(),
            "cache": await self._check_cache()
        }
```

## 🌐 Phase 4: 웹 인터페이스 및 API (2-3주)

### 4.1 REST API (FastAPI)
```python
# presentation/api/
from fastapi import FastAPI, Depends
from dependency_injector.wiring import Provide, inject

app = FastAPI(title="Value Screener API")

@app.post("/screening/run")
@inject
async def run_screening(
    request: ScreeningRequest,
    screener: ScreeningService = Depends(Provide[Container.screening_service])
):
    return await screener.run_screening(request)
```

### 4.2 웹 UI (Streamlit)
```python
# presentation/web/
import streamlit as st

def main():
    st.title("Value Screener Dashboard")
    
    # 종목 입력
    tickers = st.text_input("종목 코드 (쉼표로 구분)")
    
    # 전략 선택
    strategy = st.selectbox("스크리닝 전략", ["Value", "Growth", "Quality"])
    
    if st.button("스크리닝 실행"):
        results = run_screening(tickers.split(","), strategy)
        st.dataframe(results)
```

## 🔧 Phase 5: 고급 기능 (3-4주)

### 5.1 백테스팅 시스템
```python
# business/backtesting/
class BacktestEngine:
    def run_backtest(self, strategy: ScreeningStrategy, 
                    start_date: datetime, end_date: datetime) -> BacktestResults:
        # 과거 데이터로 전략 성과 검증
        pass
```

### 5.2 포트폴리오 최적화
```python
# business/portfolio/
class PortfolioOptimizer:
    def optimize_weights(self, stocks: List[Stock], 
                        method: str = "mean_variance") -> Dict[str, float]:
        # 포트폴리오 가중치 최적화
        pass
```

### 5.3 실시간 알림 시스템
```python
# infrastructure/notifications/
class NotificationService:
    async def send_alert(self, message: str, channels: List[str]):
        # 이메일, 슬랙, 텔레그램 등으로 알림 전송
        pass
```

## 📈 성능 목표

### 현재 vs 목표
| 지표 | 현재 | 목표 |
|------|------|------|
| 종목당 처리 시간 | ~2초 | ~0.5초 |
| 동시 처리 종목 수 | 8개 | 50개 |
| 메모리 사용량 | ~100MB | ~200MB |
| API 응답 시간 | N/A | <500ms |

## 🛠️ 기술 스택 확장

### 추가 라이브러리
```toml
# pyproject.toml
dependencies = [
    # 기존 의존성...
    "fastapi>=0.100.0",           # REST API
    "uvicorn>=0.23.0",            # ASGI 서버
    "streamlit>=1.25.0",          # 웹 UI
    "redis>=4.6.0",               # 캐싱
    "aiohttp>=3.8.0",             # 비동기 HTTP
    "structlog>=23.0.0",          # 구조화된 로깅
    "dependency-injector>=4.41.0", # DI 컨테이너
    "prometheus-client>=0.17.0",   # 메트릭 수집
    "pytest-asyncio>=0.21.0",     # 비동기 테스트
]
```

## 🎯 구현 우선순위

1. **High Priority**: 레이어드 아키텍처, DI 컨테이너, 인터페이스 정의
2. **Medium Priority**: 플러그인 시스템, 전략 패턴, 비동기 처리
3. **Low Priority**: 웹 UI, 백테스팅, 포트폴리오 최적화

이 로드맵을 통해 Value Screener를 확장 가능하고 유지보수하기 쉬운 시스템으로 발전시킬 수 있습니다.
