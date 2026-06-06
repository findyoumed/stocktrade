# 작업 로그 (WORK_LOG)

## [2026-06-04 19:40] Streamlit 배포 의존성 에러 해결 시작

**LOG_ID: 20260604_1940**
목표: Streamlit Cloud 배포 중 발생한 `ModuleNotFoundError: No module named 'yfinance'` 에러를 해결하기 위해 `requirements.txt` 파일을 확인하고 수정함.

### 계획
1. GitHub 리포지토리 (`https://github.com/findyoumed/stocktrade.git`)를 로컬 workspace (`d:\work\stock`)에 복제(Clone).
2. 복제 완료 후, 리포지토리 루트 또는 app 폴더에 `requirements.txt`가 존재하는지 확인.
3. `requirements.txt` 파일에 `yfinance` 및 대시보드 구동에 필요한 라이브러리 목록이 정의되어 있는지 점검하고, 누락된 `yfinance` 추가.
4. 로컬에서 파이썬 문법 검증 및 `requirements.txt` 정상 반영 확인.
5. 변경 사항을 Git 커밋 및 Push하여 Streamlit Cloud에서 자동으로 다시 배포 및 정상 동작하는지 확인하도록 유도.

### 수행 작업
1. Git 리포지토리를 로컬 workspace `d:\work\stock`에 받아옴.
2. `requirements.txt` 파일에 누락된 `yfinance` 및 `requests` 패키지 추가 (`requirements.txt`에 `LOG_ID: 20260604_1940` 주석 추가).
3. 로컬에서 `pip install -r requirements.txt` 명령을 수행하여 정상적으로 패키지가 다운로드 및 설치됨을 확인 (검증 완료).

### 결과
- ✅ 성공: `requirements.txt` 포맷 및 의존성 분석 통과, 로컬 환경에서 설치 완료.

---

## [2026-06-04 19:52] plus_dividend 리포지토리 분석 및 주식 대시보드 개선

**LOG_ID: 20260604_1952**
목표: `https://github.com/findyoumed/plus_dividend` 프로젝트에서 배울 수 있는 코드/로직을 분석하여 현재 주식 대시보드(`chapter3/stock_prediction_dashboard.py`)에 이식 및 보완.

### 계획
1. `https://github.com/findyoumed/plus_dividend` 리포지토리를 로컬 임시 폴더(`d:\work\stock\plus_dividend_temp`)에 클론.
2. 클론된 리포지토리 내의 주요 코드(파이썬 파일 등)를 분석하여 배당 분석 관련 주요 알고리즘 및 시각화 로직을 추출.
3. 현재 대시보드(`chapter3/stock_prediction_dashboard.py`)와 비교하여 개선 및 이식할 영역 정의.
4. 대시보드 코드에 해당 배당 분석/예측 또는 시각화 기능 추가 구현.
5. 파이썬 문법 에러 및 로컬 Streamlit 실행 상태 확인.
6. 완료 후 임시 폴더 삭제 및 Git에 변경 사항 스테이징/커밋.

### 예상 시간
- 20분 내외

### 변경 파일 수
- `chapter3/stock_prediction_dashboard.py` (1개 파일 수정)

## [2026-06-04 20:00] ETF 검색 결과 행 클릭 시 자동 입력 구현

**LOG_ID: 20260604_2000**
목표: ETF 및 키워드 검색 결과 표에서 행을 클릭하면 해당 티커가 사이드바 입력창에 자동 입력되도록 수정
변경 파일: chapter3/stock_prediction_dashboard.py
수행 작업: 1) 세션 상태에 target_ticker 초기화 2) st.dataframe에 on_select 속성 추가 3) 사이드바 st.text_input에 key='target_ticker' 연동
실행: streamlit run chapter3/stock_prediction_dashboard.py`n기대: 우측 표에서 행 클릭 시 왼쪽 사이드바 입력창에 티커 자동 입력
결과: ✅ 대기 중

## [2026-06-04 23:05] 사이드바 UI 텍스트 통일성 개선

**LOG_ID: 20260604_2305**
목표: 사이드바의 지수/ETF 리스트 영역과 종목 검색 입력창의 레이블 텍스트 및 아이콘을 통일감 있게 수정
변경 파일: chapter3/stock_prediction_dashboard.py
수행 작업: 1) st.sidebar.expander 라벨을 '🔍 지수/ETF 카테고리 검색'으로 변경 2) st.sidebar.text_input 라벨을 '🔍 종목 코드/종목명 직접 입력 (예: SPY, 삼성전자, 005930)'으로 변경
실행: streamlit run chapter3/stock_prediction_dashboard.py
기대: 사이드바의 두 검색/입력 영역이 시각적으로 통일감을 주고 가독성이 높아짐
결과: ✅ 성공

---

## [2026-06-06 20:05] 변동성 돌파 전략(VBT) 배당금 반영 오류 해결 및 검증

**LOG_ID: 20260606_2005**
목표: 변동성 돌파 전략(VBT)의 백테스트 수익률 계산 시 배당금 재투자(DRIP) 설정이 켜져 있어도 배당수익률(`strategy_div_yield`)이 전략 일별 수익률(`Strategy_Return`)에 누락되는 오류를 수정하고 검증.
변경 파일:
- `chapter3/backtest_engine.py` (VBT 백테스트 엔진 로직 수정)
- `chapter3/stock_prediction_dashboard.py` (대시보드 내 내장 VBT 백테스트 로직 수정)
수행 작업:
1. `run_vbt_backtest` 함수에서 `use_drip`이 참이고 `배당금` 컬럼이 존재할 때 `strategy_div_yield`를 계산하도록 로직 추가.
2. 매수 진입 시점(`Buy_Signal`이 True인 날)에만 배당수익률이 주식 잔고에 재투자되도록 `Strategy_Return`에 `strategy_div_yield`를 더해 줌.
3. 비거래일(신호 없음)의 fallback 수익률이 1.0에서 잘못 차감되지 않도록 1.0 유지 처리 확인.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: 변동성 돌파 전략 백테스트 시 배당금 재투자(DRIP) 체크박스를 켜면 최종 수익률 및 잔고 지표가 배당금을 포함하여 정상적으로 상승함.
결과: ✅ 성공

---

## [2026-06-06 20:21] MACD 추세 전략 추가 구현

**LOG_ID: 20260606_2021**
목표: 이동평균선(MA) 크로스 전략보다 민감도가 높고 퀀트 투자에 널리 활용되는 MACD 추세 추종 전략을 신규 전략으로 추가 구현.
변경 파일:
- `chapter3/backtest_engine.py` (MACD 지표 산출, 백테스트 및 월별 요약 통계 함수 추가)
- `chapter3/stock_prediction_dashboard.py` (사이드바 선택 옵션, 슬라이더 파라미터 연동, 결과 시각화(주가+MACD 2단 차트) 구현)
수행 작업:
1. `backtest_engine.py`에 단기 EMA, 장기 EMA, Signal EMA 기반의 MACD 계산 및 시그널선 골든/데드 크로스 거래 연산 함수 구현.
2. 대시보드 사이드바의 전략 선택 라디오 버튼에 "MACD 추세 전략"을 추가하고 관련 슬라이더(12, 26, 9 기본값) 배치.
3. 성과 지표(Metrics), 누적 수익률 비교 추이 및 월별 통계 테이블에 연동 처리.
4. 주가 차트 하단에 MACD선, Signal선, 히스토그램(오실레이터 막대 차트)이 연동되는 2단 보조지표 차트 시각화 구성.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: 대시보드에서 MACD 추세 전략 선택 시 실시간 보조지표 차트가 렌더링되며 백테스트 성과 분석이 수행됨.
결과: ✅ 성공

---

## [2026-06-06 21:18] 백테스트 실행하기 버튼 위치 이동

**LOG_ID: 20260606_2118**
목표: 사이드바에서 "🚀 백테스트 실행하기" 버튼을 "시작 날짜 (YYYYMMDD)" 입력 칸 바로 위로 배치 이동.
변경 파일:
- `chapter3/stock_prediction_dashboard.py` (버튼 렌더링 코드 위치 이동)
수행 작업:
- 원래 종목 코드 직접 입력 영역 바로 밑(라인 1123 부근)에 있던 버튼 생성 코드를 "💡 분석할 전략 선택" 라디오 버튼 바로 아래이자 "시작 날짜 (YYYYMMDD)" 입력 칸 바로 위로 순서를 변경함.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: 사이드바 UI에서 백테스트 실행하기 버튼이 시작 날짜 위에 정확히 렌더링됨.
결과: ✅ 성공

---

## [2026-06-06 21:36] 전략별 동적 설명 카드 추가

**LOG_ID: 20260606_2136**
목표: 사용자가 왼쪽 사이드바에서 전략을 바꿀 때마다 각 전략이 어떤 원리와 조건으로 작동하는지 우측 본문 상단에 설명 카드로 동적 노출하도록 개선.
변경 파일:
- `chapter3/stock_prediction_dashboard.py` (전략 설명 매핑 테이블 및 동적 카드 렌더링 코드 추가)
수행 작업:
- `STRATEGY_DESCRIPTIONS` 딕셔너리를 신설하여 머신러닝, 변동성 돌파, 듀얼 모멘텀, 이평선 골든크로스, RSI 반등, 볼린저 밴드, MACD 전략의 원리, 매매 규칙, 특징을 알기 쉬운 마크다운 텍스트로 정의함.
- 사용자가 선택한 `strategy_choice`에 매칭되는 마크다운 설명을 본문 예외처리 및 데이터 검증 직전 단계에서 `st.info()`를 사용해 상시 표시하도록 구현함.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: 라디오 버튼 클릭으로 전략을 전환할 때마다 본문 상단 설명 상자 내 텍스트가 즉각 업데이트되어 사용자가 바로 원리를 이해할 수 있음.
결과: ✅ 성공

---

## [2026-06-07 00:53] 정적 포트폴리오(올웨더/영구) 월별 요약 테이블 통계 개선

**LOG_ID: 20260607_0053**
목표: 올웨더 및 영구 포트폴리오와 같은 정적 자산 배분 전략 수행 시, 월별 요약 데이터 표에서 상시 보유 상태임에도 '매수 보유 일수'가 월초 1일(리밸런싱 당일)로 표시되던 버그 수정.
변경 파일:
- `chapter3/stock_prediction_dashboard.py` (calculate_signal_monthly_stats 함수 로직 및 메인 호출부 보완)
수행 작업:
- `calculate_signal_monthly_stats` 함수에 `is_portfolio` 매개변수를 추가하고, 월간 전체 실제 영업일 수(`Working_Days` 합계)를 별도 계산하도록 설계함.
- 정적 자산 배분 포트폴리오 전략일 경우에는 '매수 보유 일수 (일)'를 한 달간의 전체 영업일 수로 치환하고, 기존 1일로 떴던 리밸런싱 날짜 합산 값을 '리밸런싱 횟수 (회)'라는 새로운 컬럼으로 구성하여 표 순서를 재정렬해 렌더링하도록 변경함.
- 메인 UI 호출부에서 영구/올웨더 포트폴리오 감지 시 `is_portfolio=True`를 전달하도록 바인딩함.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: 올웨더 및 영구 포트폴리오 백테스트 시 월별 테이블에 보유 일수가 영업일 기준 한 달치 전체(예: 20~22일)로 정상 집계되고, 리밸런싱 횟수는 '1회'로 명확히 표시됨.
결과: ✅ 성공

---

## [2026-06-07 00:54] 영문 2글자 그룹사 검색어(lg, sk 등) 필터링 소실 에러 수정

**LOG_ID: 20260607_0054**
목표: `lg`, `sk` 등 대기업 그룹사 2글자 영문명 검색 시, 내부 특수문자용 1글자 영문 토큰 필터링 로직에 의해 검색어가 소실되어 계열사가 검색 결과에 안 뜨던 버그 수정.
변경 파일:
- `chapter3/stock_prediction_dashboard.py` (search_local_tickers 함수 내 토큰 필터 조건식 수정)
수행 작업:
- 원래 한 글자 알파벳 오염 방지를 위해 1글자 토큰을 일괄 제거하던 로직에 원본 정규화 검색어 길이 판별을 추가함.
- `len(original_compact) > 2` 조건을 씌워, 사용자가 입력한 검색어 자체가 2글자 이하의 짧은 약어일 때는 한 글자(l, g 등) 영문 토큰이 필터링에 의해 유실되는 것을 방어하도록 코드 수정함.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: `lg` 검색창 입력 시 'l'과 'g' 토큰이 삭제되지 않고 정상 보존되어 LG, LG화학, LG전자, LG유플러스 등 전체 매칭 리스트가 올바르게 검색 결과 표에 출력됨.
결과: ✅ 성공

---

## [2026-06-07 00:56] 영어 그룹사 검색 시 미국 주식 티커 매칭 오작동 수정

**LOG_ID: 20260607_0056**
목표: `sk`, `lg` 등 2글자 영어 기업명을 검색창에 입력하면 미국 주식 티커(예: SPY 등)로 오인되어 단일 매칭 외의 국내 계열사들(예: SK하이닉스, LG화학 등)이 검색 드롭다운 필터에서 삭제되거나 "알 수 없는 종목" 에러를 내던 오류 해결.
변경 파일:
- `chapter3/stock_prediction_dashboard.py` (사이드바 종목 코드 입력 바인딩 영역 보완)
수행 작업:
- 입력된 문자가 영문 티커 형식인지 판별하는 `is_ticker_like_input` 로직 직전에 `is_group_name_search` 우회 검증을 도입함.
- 사용자 입력어가 대문자/소문자 기준 `["lg", "sk", "gs", "cj", "hd"]`에 포함되는 경우, 미국 티커 필터링 연산을 건너뛰도록 구조화하여 국내 매칭 후보 전체가 원본 유지되도록 개선함.
실행: `streamlit run chapter3/stock_prediction_dashboard.py`
기대: `sk` 검색창 입력 시 "알 수 없는 종목" 에러가 나지 않고 SK, SK하이닉스, SK텔레콤 등 관련 목록이 드롭다운에 모두 정상 팝업되며, `lg` 역시 LG 계열사들이 한 화면에 전부 표기됨.
결과: ✅ 성공


