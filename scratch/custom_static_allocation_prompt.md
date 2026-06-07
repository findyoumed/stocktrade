# 사용자 정의 정적 자산배분 전략 구현 프롬프트

아래 요청을 현재 Python Streamlit 주식 백테스트 대시보드 프로젝트에 적용해줘.

## 목표

현재 대시보드에 **사용자 정의 정적 자산배분 전략**을 추가한다.

이 전략은 특정 티커 전용 전략이 아니다. 사용자가 직접 여러 ETF 티커와 목표 비중을 입력하면, 초기 투자금을 해당 비중대로 배분하고, 선택한 주기마다 목표 비중으로 다시 맞추는 포트폴리오 백테스트 전략이다.

예시:

```text
VOO 50%
QQQ 30%
TLT 20%
```

이런 전략은 보통 **정적 자산배분 + 리밸런싱 전략**이라고 부른다.

정적 자산배분은 목표 비중을 정해두는 것이고, 리밸런싱은 시간이 지나면서 틀어진 실제 비중을 다시 목표 비중으로 맞추는 행위다.

## 작업 전 확인

1. 기존 코드 구조를 먼저 확인한다.
2. 기존 백테스트 엔진과 대시보드 패턴을 최대한 따른다.
3. 기존 사용자 변경사항을 되돌리지 않는다.
4. 관련 없는 리팩터링이나 포맷팅 변경은 하지 않는다.
5. `scratch/test_backtest.py`처럼 이미 수정된 파일이 있으면 사용자 변경일 수 있으므로 건드리지 않는다.

주요 파일 후보:

```text
chapter3/backtest_engine.py
chapter3/stock_prediction_dashboard.py
```

## 이번 범위에 포함할 것

- 미국 ETF 같은 동일 시장 ETF 중심 정적 자산배분
- 최대 5개 ETF 입력
- 목표 비중 합계 100% 검증
- 월말/분기말/연말/리밸런싱 없음 선택
- 수수료/슬리피지 반영
- 소수점 수량 매수 허용
- 포트폴리오 누적 수익률 계산
- 기준 ETF 단순 보유와 비교
- 월별 수익률 요약
- 자산별 비중 변화 확인

## 이번 범위에서 제외할 것

처음 구현은 단순하고 안정적으로 만든다. 아래 기능은 이번 범위에서 제외한다.

- 세금 반영
- 환율 반영
- 환전 수수료 반영
- 정수 주식 수량만 허용하는 현실 매매
- 배당락일 정밀 조정
- 한국/미국 혼합 시장 정밀 처리
- 적립식 DCA 포트폴리오
- 연금계좌/ISA/일반계좌별 세제 구분

## UI 요구사항

사이드바의 전략 선택 라디오에 아래 전략을 추가한다.

```text
사용자 정의 정적 자산배분 전략
```

위 전략을 선택하면 사이드바의 전략 파라미터 영역에 포트폴리오 입력 UI를 보여준다.

입력 UI는 처음에는 단순하게 최대 5개 고정 행으로 구성한다.

기본값:

```text
자산 1 티커: VOO
자산 1 비중: 50

자산 2 티커: QQQ
자산 2 비중: 30

자산 3 티커: TLT
자산 3 비중: 20

자산 4 티커: 빈칸
자산 4 비중: 0

자산 5 티커: 빈칸
자산 5 비중: 0
```

리밸런싱 주기 선택 UI:

```text
월말
분기말
연말
리밸런싱 없음
```

검증 UI:

- 빈 티커 또는 비중 0인 행은 무시한다.
- 비중 합계가 100%가 아니면 백테스트를 실행하지 않고 에러 메시지를 보여준다.
- 같은 티커가 중복 입력되면 백테스트를 실행하지 않고 에러 메시지를 보여준다.
- 유효한 자산이 1개 미만이면 에러 메시지를 보여준다.
- 가능하면 현재 입력된 비중 합계를 사이드바 caption/info로 보여준다.

예시 메시지:

```text
비중 합계: 100.00% 정상
```

또는

```text
비중 합계가 100%가 아닙니다. 현재 합계: 95.00%
```

## 백테스트 엔진 요구사항

`chapter3/backtest_engine.py`에 새 함수를 추가한다.

함수명 예시:

```python
run_custom_static_allocation_backtest
```

입력값 예시:

```python
def run_custom_static_allocation_backtest(
    asset_data,
    target_weights,
    initial_budget,
    fee_rate_pct,
    slippage_rate_pct,
    rebalance_frequency="M",
):
    ...
```

인자 의미:

```text
asset_data:
    티커별 OHLCV DataFrame 딕셔너리
    예: {"VOO": voo_df, "QQQ": qqq_df, "TLT": tlt_df}

target_weights:
    티커별 목표 비중 딕셔너리
    예: {"VOO": 0.5, "QQQ": 0.3, "TLT": 0.2}

initial_budget:
    초기 투자금

fee_rate_pct:
    수수료율(%)

slippage_rate_pct:
    슬리피지율(%)

rebalance_frequency:
    "M" = 월말
    "Q" = 분기말
    "Y" = 연말
    None = 리밸런싱 없음
```

## 데이터 정렬 방식

처음 구현은 동일 시장 ETF 중심이므로 단순하게 처리한다.

권장 방식:

1. 각 자산의 `종가` 컬럼을 하나의 가격 테이블로 합친다.
2. 날짜 기준으로 정렬한다.
3. 가격이 없는 날짜는 `ffill()`로 보정한다.
4. 모든 자산 가격이 유효한 첫 날짜부터 백테스트를 시작한다.

예:

```python
prices = pd.DataFrame({
    ticker: df["종가"]
    for ticker, df in asset_data.items()
}).sort_index().ffill().dropna()
```

주의:

- 동일 시장 ETF 중심이라는 전제에서는 `ffill()`이 실용적이다.
- 한국/미국 혼합 시장까지 정밀하게 다루는 것은 이번 범위가 아니다.

## 수학적 계산 로직

### 1. 초기 투자

첫 거래일 가격을 기준으로 초기 투자금을 목표 비중대로 나눈다.

```text
Target_Value_i = Initial_Budget × Target_Weight_i
Shares_i = Target_Value_i / Price_i
```

수수료/슬리피지를 반영한다.

거래 비용:

```text
Cost_Rate = (Fee_Rate_Pct + Slippage_Rate_Pct) / 100
Trade_Cost_i = Target_Value_i × Cost_Rate
```

단순화를 위해 소수점 수량을 허용한다.

비용 반영 방식은 두 가지 중 하나를 일관되게 선택한다.

권장 방식:

```text
실제 매수 가능 금액 = Target_Value_i × (1 - Cost_Rate)
Shares_i = 실제 매수 가능 금액 / Price_i
```

### 2. 일별 평가

매일 포트폴리오 평가금액을 계산한다.

```text
Asset_Value_i,t = Shares_i,t × Price_i,t
Portfolio_Value_t = Σ Asset_Value_i,t + Cash_t
```

각 자산 비중:

```text
Weight_i,t = Asset_Value_i,t / Portfolio_Value_t
```

### 3. 리밸런싱 날짜 계산

리밸런싱 주기에 따라 날짜를 정한다.

월말:

```python
rebalance_dates = prices.groupby(prices.index.to_period("M")).tail(1).index
```

분기말:

```python
rebalance_dates = prices.groupby(prices.index.to_period("Q")).tail(1).index
```

연말:

```python
rebalance_dates = prices.groupby(prices.index.to_period("Y")).tail(1).index
```

리밸런싱 없음:

```python
rebalance_dates = []
```

### 4. 리밸런싱 거래

리밸런싱 날짜에는 현재 총자산을 목표 비중대로 다시 나눈다.

현재 자산별 평가금액:

```text
Current_Value_i,t = Shares_i,t × Price_i,t
```

목표 자산별 평가금액:

```text
Target_Value_i,t = Portfolio_Value_t × Target_Weight_i
```

매매금액:

```text
Trade_Value_i,t = Target_Value_i,t - Current_Value_i,t
```

수수료/슬리피지:

```text
Trade_Cost_t = Σ abs(Trade_Value_i,t) × Cost_Rate
```

비용 차감 후 리밸런싱:

```text
Portfolio_Value_After_Cost = Portfolio_Value_t - Trade_Cost_t
Final_Target_Value_i,t = Portfolio_Value_After_Cost × Target_Weight_i
Shares_i,t = Final_Target_Value_i,t / Price_i,t
Cash_t = 0
```

### 5. 일별 수익률

포트폴리오 전략 일별 수익률:

```text
Strategy_Return_t = Portfolio_Value_t / Portfolio_Value_{t-1}
```

리밸런싱 비용이 발생한 날에는 비용 반영 후의 포트폴리오 가치로 수익률을 계산한다.

누적 수익률:

```text
Strategy_Cum_Return_t = (cumprod(Strategy_Return) - 1) × 100
```

전략 잔고:

```text
Strategy_Balance_t = Initial_Budget × cumprod(Strategy_Return)
```

## 비교 기준

기준 성과는 **첫 번째 입력 ETF 단순 보유**로 둔다.

예:

```text
VOO 50%
QQQ 30%
TLT 20%
```

이 경우 기준은 VOO 단순 보유다.

기준 ETF 단순 보유 수익률:

```text
Hold_Return_t = Price_first_asset_t / Price_first_asset_{t-1}
Hold_Cum_Return_t = (cumprod(Hold_Return) - 1) × 100
Hold_Balance_t = Initial_Budget × cumprod(Hold_Return)
```

가능하면 나중에 확장할 수 있도록 **무리밸런싱 포트폴리오** 비교 구조도 열어두면 좋다. 하지만 첫 구현에서는 필수는 아니다.

## 결과 DataFrame 요구 컬럼

결과 DataFrame에는 최소한 아래 컬럼을 포함한다.

```text
Strategy_Return
Strategy_Cum_Return
Strategy_Balance
Hold_Return
Hold_Cum_Return
Hold_Balance
Daily_Return_Pct
Rebalance_Signal
Trade_Cost
Selected_Asset 또는 Portfolio_Label
```

자산별 컬럼도 추가한다.

예:

```text
VOO_Value
QQQ_Value
TLT_Value

VOO_Weight
QQQ_Weight
TLT_Weight

VOO_Shares
QQQ_Shares
TLT_Shares
```

## 월별 통계 함수

월별 요약 함수도 추가한다.

함수명 예시:

```python
calculate_custom_static_allocation_monthly_stats
```

월별 통계에는 최소한 아래 값을 포함한다.

```text
년-월
리밸런싱 횟수 (회)
전략 수익률 (%)
기준 ETF 단순 보유 수익률 (%)
```

가능하면 월말 자산 비중도 포함한다.

예:

```text
월말 VOO 비중 (%)
월말 QQQ 비중 (%)
월말 TLT 비중 (%)
```

## 대시보드 실행 분기

`chapter3/stock_prediction_dashboard.py`에서 기존 전략들과 같은 패턴으로 연결한다.

전략 선택 목록에 추가:

```text
사용자 정의 정적 자산배분 전략
```

전략 파라미터 영역에 입력 UI 추가:

```python
elif strategy_choice == "사용자 정의 정적 자산배분 전략":
    ...
```

백테스트 실행 분기 추가:

```python
elif strategy_choice == "사용자 정의 정적 자산배분 전략":
    ...
```

여기서 해야 할 일:

1. 입력된 티커/비중을 정리한다.
2. 비중 합계 100%를 검증한다.
3. 중복 티커를 검증한다.
4. 각 ETF 데이터를 `load_data(start_date, end_date, ticker)`로 불러온다.
5. 데이터 로드 실패 시 에러를 보여주고 중단한다.
6. `run_custom_static_allocation_backtest(...)`를 호출한다.
7. 결과값에서 최종 잔고, 누적 수익률, 리밸런싱 횟수, 총 분석일 수를 계산한다.

## 메인 화면 출력 요구사항

기존 백테스트 결과 UI 패턴을 재사용한다.

상단 metric:

```text
전략 최종 잔고 / 수익률
기준 ETF 단순 보유 최종 잔고 / 수익률
총 리밸런싱 횟수
총 분석 영업일 수
```

가격/비중 차트:

1. 포트폴리오 누적 수익률 vs 기준 ETF 단순 보유 누적 수익률
2. 자산별 비중 변화 차트

비중 변화 차트는 stacked area chart가 적합하다.

예:

```python
fig_weights = go.Figure()
for ticker in tickers:
    fig_weights.add_trace(go.Scatter(
        x=result.index,
        y=result[f"{ticker}_Weight"] * 100,
        stackgroup="one",
        name=ticker,
    ))
```

월별 통계:

```text
년-월
리밸런싱 횟수
전략 수익률
기준 ETF 단순 보유 수익률
월말 자산별 비중
```

## 기존 UI와의 관계

현재 대시보드에는 이미 아래 전략이 있다.

```text
영구 포트폴리오 전략
올웨더 포트폴리오 전략
```

새 전략은 이 둘과 성격이 비슷하다.

차이점:

```text
영구 포트폴리오: 고정된 자산 구성
올웨더 포트폴리오: 고정된 자산 구성
사용자 정의 정적 자산배분: 사용자가 ETF와 비중을 직접 입력
```

따라서 UI상으로는 영구 포트폴리오/올웨더 포트폴리오 근처에 배치하는 것이 자연스럽다.

## 검증

최소 검증:

```powershell
python -m py_compile chapter3\backtest_engine.py chapter3\stock_prediction_dashboard.py
```

가능하면 짧은 기간으로 앱 실행도 확인한다.

예:

```powershell
streamlit run chapter3/stock_prediction_dashboard.py
```

테스트 시 예시 포트폴리오:

```text
VOO 50
QQQ 30
TLT 20
```

시작일/종료일 예:

```text
20200101 ~ 현재
```

확인할 것:

- 비중 합계 100%일 때 정상 실행되는가
- 비중 합계가 100%가 아니면 실행이 막히는가
- 중복 티커가 있으면 실행이 막히는가
- 빈 티커/0% 비중 행은 무시되는가
- 리밸런싱 횟수가 월말/분기말/연말 선택에 따라 달라지는가
- 결과 차트와 월별 표가 깨지지 않는가

## 주의사항

이 전략은 MACD나 RSI처럼 단일 `Buy_Signal`로 사고파는 전략이 아니다.

핵심은 다음이다.

```text
목표 비중 유지
자산별 평가금액 계산
리밸런싱 날짜에 비중 재조정
리밸런싱 비용 차감
포트폴리오 전체 잔고 계산
```

따라서 기존 신호 기반 전략에 억지로 끼워 넣지 말고, 포트폴리오 전용 백테스트 함수로 구현하라.

처음부터 너무 많은 현실 요소를 넣지 말고, **동일 시장 ETF 중심의 단순하고 안정적인 정적 자산배분 백테스트**를 완성하는 데 집중하라.
