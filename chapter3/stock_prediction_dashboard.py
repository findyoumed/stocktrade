import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path

# [LOG: 20260604_1357]

UNKNOWN_TICKER_NAME = "알 수 없는 종목"
INVALID_TICKER_HINTS = {
    "396580": "ACE 미국30년국채액티브(H)의 종목코드는 453850입니다."
}


def configure_yfinance_cache(yf):
    """yfinance가 쓰는 로컬 캐시를 프로젝트 내부로 고정합니다."""
    cache_dir = Path(__file__).resolve().parents[1] / ".cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))

# 1. 종목 이름 조회 함수 (pykrx와 yfinance를 모두 활용하여 미국 주식 및 국내 ETF 지원)
def get_ticker_name(ticker_code):
    """종목 코드를 받아 종목명을 반환합니다. (예: 005930 -> 삼성전자, TLT -> iShares 20+ Year Treasury Bond ETF)"""
    ticker_code = ticker_code.strip()
    if not ticker_code:
        return UNKNOWN_TICKER_NAME
    
    etf_map = {
        "360750": "TIGER 미국S&P500",
        "379800": "KODEX 미국S&P500TR",
        "365000": "ACE 미국S&P500",
        "314250": "KODEX 미국나스닥100TR",
        "133690": "TIGER 미국나스닥100",
        "252670": "KODEX 200선물인버스2X",
        "114800": "KODEX 인버스",
        "122630": "KODEX 레버리지",
        "453850": "ACE 미국30년국채액티브(H)",  # 국내상장 TLT 추종 ETF
        "476560": "KODEX 미국30년국채액티브(H)", # 국내상장 TLT 추종 ETF
        "458250": "TIGER 미국30년국채액티브(H)"  # 국내상장 TLT 추종 ETF
    }
    
    if ticker_code in etf_map:
        return etf_map[ticker_code]
        
    # 영어 종목코드 (미국 주식)인 경우 yfinance로 조회
    if ticker_code.isalpha():
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            ticker_info = yf.Ticker(ticker_code.upper()).info
            name = ticker_info.get('longName') or ticker_info.get('shortName')
            if name:
                return name
        except Exception:
            pass
        return UNKNOWN_TICKER_NAME
            
    # 숫자 종목코드 (한국 주식)인 경우 pykrx로 먼저 조회
    try:
        name = stock.get_market_ticker_name(ticker_code)
        if name != "":
            return name
    except Exception:
        pass
        
    # pykrx로 조회가 안 되는 경우 yfinance(.KS)로 재차 조회
    try:
        import yfinance as yf
        configure_yfinance_cache(yf)
        ticker_info = yf.Ticker(f"{ticker_code}.KS").info
        name = ticker_info.get('longName') or ticker_info.get('shortName')
        if name:
            return name
    except Exception:
        pass
        
    return UNKNOWN_TICKER_NAME

# 2. 주식 데이터 불러오기 함수 (pykrx 실패 시 yfinance로 백업 연동 및 미국 주식 직접 조회 기능 추가)
@st.cache_data
def load_data(start_date, end_date, ticker_code):
    """선택한 종목의 주식 데이터를 불러옵니다. pykrx와 yfinance를 연계합니다."""
    ticker_code = ticker_code.strip()
    
    # 1. 영어 종목코드 (미국 주식, 예: TLT, SPY, QQQ)인 경우 yfinance로 즉시 로딩
    if ticker_code.isalpha():
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            df = yf.download(ticker_code.upper(), start=start_yf, end=end_yf)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                df = df.rename(columns={
                    'Open': '시가',
                    'High': '고가',
                    'Low': '저가',
                    'Close': '종가',
                    'Volume': '거래량'
                })
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df
        except Exception as e:
            st.error(f"미국 주식 yfinance 데이터 로드 실패: {e}")
            return pd.DataFrame()
            
    # 2. 숫자 종목코드 (한국 주식/ETF)인 경우
    df = pd.DataFrame()
    try:
        # 1차 시도: pykrx
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker_code)
    except Exception:
        pass
        
    # 2차 시도: pykrx 데이터가 비어있을 경우 yfinance의 한국 소스(.KS)로 백업 다운로드
    if df.empty and len(ticker_code) == 6 and ticker_code.isdigit():
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            df = yf.download(f"{ticker_code}.KS", start=start_yf, end=end_yf)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                df = df.rename(columns={
                    'Open': '시가',
                    'High': '고가',
                    'Low': '저가',
                    'Close': '종가',
                    'Volume': '거래량'
                })
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df
        except Exception as e:
            st.error(f"한국 ETF yfinance 백업 데이터 로드 실패: {e}")
            return pd.DataFrame()
            
    return df

# 3. 머신러닝 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

# 4. 머신러닝 롤링 윈도우 예측 수행 함수
@st.cache_data
def run_rolling_forecast(X, y, window_size):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 종가를 예측합니다. 
    동일한 피처와 윈도우 크기일 경우 연산 결과를 캐싱하여 즉시 반환합니다.
    """
    predictions = []
    prediction_dates = []
    
    # 진행 상황 표시줄
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_steps = len(X) - window_size
    
    for i in range(window_size, len(X)):
        # 학습 데이터 슬라이싱
        X_train = X.iloc[i-window_size:i]
        y_train = y.iloc[i-window_size:i]
        
        # 예측 대상 하루
        X_test = X.iloc[[i]]
        
        # 모델 생성 및 학습
        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # 예측 및 결과 저장
        pred = model.predict(X_test)[0]
        predictions.append(pred)
        prediction_dates.append(X.index[i])
        
        # 프로그레스바 업데이트
        current_step = i - window_size + 1
        progress_bar.progress(current_step / total_steps)
        status_text.text(f"머신러닝 예측 진행 중: {current_step}/{total_steps} 영업일 완료...")
        
    progress_bar.empty()
    status_text.empty()
    
    pred_series = pd.Series(predictions, index=prediction_dates)
    return pred_series

# 5. 머신러닝 백테스트 수익률 계산 함수 (실전 수수료/슬리피지 비용 반영)
def run_ml_backtest(df, pred_series, initial_budget, fee_rate_pct, slippage_rate_pct):
    """예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    backtest_df = pd.DataFrame({
        'Actual_Close': df['종가'].loc[pred_series.index],
        'Predicted_Close': pred_series,
        'Prev_Close': df['종가'].shift(1).loc[pred_series.index]
    }).dropna()
    
    backtest_df['Buy_Signal'] = backtest_df['Predicted_Close'] > backtest_df['Prev_Close']
    
    # 이전 영업일 매수 포지션 여부
    prev_signals = backtest_df['Buy_Signal'].shift(1).fillna(False)
    
    # 포지션 변동(진입/청산) 시 거래 비용 차감
    entry_cost = np.where((backtest_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
    total_cost = entry_cost + exit_cost
    
    # 전략 일별 수익률 계산
    backtest_df['Strategy_Return'] = np.where(
        backtest_df['Buy_Signal'],
        (backtest_df['Actual_Close'] / backtest_df['Prev_Close']) - total_cost,
        1.0 - total_cost
    )
    
    # 단순 보유 일별 수익률 (최초 1회 매수 수수료 반영)
    hold_returns = backtest_df['Actual_Close'] / backtest_df['Prev_Close']
    hold_returns_array = hold_returns.values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    backtest_df['Hold_Return'] = hold_returns_array
    
    # 누적 수익률 계산 (%)
    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    
    # 최종 잔고 계산 (원)
    backtest_df['Strategy_Balance'] = initial_budget * backtest_df['Strategy_Return'].cumprod()
    backtest_df['Hold_Balance'] = initial_budget * backtest_df['Hold_Return'].cumprod()
    
    return backtest_df

# 6. 머신러닝 월별 백테스트 통계 계산 함수
def calculate_ml_monthly_stats(actual, predicted, backtest_df):
    """머신러닝 예측 오차 및 월별 수익률 통계를 계산합니다."""
    compare_df = pd.DataFrame({
        'Actual': actual,
        'Predicted': predicted,
        'Strategy_Return': backtest_df['Strategy_Return']
    }).dropna()
    
    compare_df['Absolute Error'] = (compare_df['Actual'] - compare_df['Predicted']).abs()
    compare_df['YearMonth'] = compare_df.index.strftime('%Y-%m')
    
    # 월별 MAE
    monthly_mae = compare_df.groupby('YearMonth')['Absolute Error'].mean().reset_index()
    monthly_mae.columns = ['년-월', '평균 절대 오차 (원)']
    
    # 월별 오차율(%)
    compare_df['Error Rate (%)'] = (compare_df['Absolute Error'] / compare_df['Actual']) * 100
    monthly_error_rate = compare_df.groupby('YearMonth')['Error Rate (%)'].mean().reset_index()
    monthly_error_rate.columns = ['년-월', '평균 오차율 (%)']
    
    # 월별 누적 수익률
    monthly_return = compare_df.groupby('YearMonth')['Strategy_Return'].prod().reset_index()
    monthly_return['Strategy_Return'] = (monthly_return['Strategy_Return'] - 1) * 100
    monthly_return.columns = ['년-월', '월간 수익률 (%)']
    
    stats_df = pd.merge(monthly_mae, monthly_error_rate, on='년-월')
    stats_df = pd.merge(stats_df, monthly_return, on='년-월')
    return stats_df

# 7. 변동성 돌파 전략 백테스트 계산 함수 (실전 수수료/슬리피지 비용 반영)
def run_vbt_backtest(df, K, initial_budget, fee_rate_pct, slippage_rate_pct):
    """변동성 돌파 전략 백테스트를 수행합니다. 
    매일 당일 진입 후 당일 청산하므로 신호 발생 시 왕복(2회) 거래 비용이 차감됩니다.
    """
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    round_trip_cost = 2 * cost_rate
    
    vbt_df = df.copy()
    
    # 변동성 폭 계산 (전일 고가 - 전일 저가)
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    
    # 매수 목표가 계산 (당일 시가 + 변동폭 * K)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    
    # 매수 조건: 당일 고가가 매수 목표가를 초과했는지 판별
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    # 전략 일별 수익률 계산 (매수 체결 시 당일 종가 / 매수 목표가 - 왕복 비용, 미체결 시 1.0)
    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        (vbt_df['종가'] / vbt_df['Buy_Target']) - round_trip_cost,
        1.0
    )
    
    # 단순 보유(Buy & Hold) 일별 수익률 (최초 1회 매수 수수료 반영)
    hold_returns = vbt_df['종가'] / vbt_df['종가'].shift(1)
    hold_returns = hold_returns.fillna(1.0)
    hold_returns_array = hold_returns.values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    vbt_df['Hold_Return'] = hold_returns_array
    
    # 누적 수익률 계산 (%)
    vbt_df['Strategy_Cum_Return'] = (vbt_df['Strategy_Return'].cumprod() - 1) * 100
    vbt_df['Hold_Cum_Return'] = (vbt_df['Hold_Return'].cumprod() - 1) * 100
    
    # 최종 잔고 계산 (원)
    vbt_df['Strategy_Balance'] = initial_budget * vbt_df['Strategy_Return'].cumprod()
    vbt_df['Hold_Balance'] = initial_budget * vbt_df['Hold_Return'].cumprod()
    
    # 일별 수익률 변동 (%)
    vbt_df['Daily_Return_Pct'] = (vbt_df['Strategy_Return'] - 1) * 100
    
    return vbt_df

# 8. 변동성 돌파 전략 월별 백테스트 통계 계산 함수
def calculate_vbt_monthly_stats(vbt_df):
    """변동성 돌파 전략의 월간 매수 횟수 및 수익률 통계를 계산합니다."""
    stats_df = vbt_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    
    summary.columns = ['년-월', '매수 횟수 (회)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

# 9. 두 전략 월별 백테스트 요약 통계 계산 함수
def calculate_combined_monthly_stats(ml_df, vbt_df):
    """두 전략의 월별 수익률 및 머신러닝 오차율을 하나의 표로 통합하여 요약합니다."""
    # 1. 머신러닝 월별 요약
    ml_df['YearMonth'] = ml_df.index.strftime('%Y-%m')
    ml_df['Absolute Error'] = (ml_df['Actual_Close'] - ml_df['Predicted_Close']).abs()
    
    ml_summary = ml_df.groupby('YearMonth').agg({
        'Absolute Error': 'mean',
        'Strategy_Return': 'prod'
    }).reset_index()
    ml_summary.columns = ['년-월', '머신러닝 오차 (원)', 'ML_Return_Prod']
    
    # 2. 변동성 돌파 월별 요약
    vbt_df['YearMonth'] = vbt_df.index.strftime('%Y-%m')
    vbt_df['Buy_Count'] = np.where(vbt_df['Buy_Signal'], 1, 0)
    
    vbt_summary = vbt_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    vbt_summary.columns = ['년-월', '돌파 매수 횟수 (회)', 'VBT_Return_Prod', 'Hold_Return_Prod']
    
    # 3. 데이터 결합 및 백분율 변환
    merged = pd.merge(ml_summary, vbt_summary, on='년-월')
    merged['머신러닝 수익률 (%)'] = (merged['ML_Return_Prod'] - 1) * 100
    merged['변동성 돌파 수익률 (%)'] = (merged['VBT_Return_Prod'] - 1) * 100
    merged['단순 보유 수익률 (%)'] = (merged['Hold_Return_Prod'] - 1) * 100
    
    final_df = merged[['년-월', '머신러닝 수익률 (%)', '변동성 돌파 수익률 (%)', '단순 보유 수익률 (%)', '돌파 매수 횟수 (회)', '머신러닝 오차 (원)']]
    return final_df

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="주식 투자 전략 백테스트 종합 비교 대시보드", layout="wide")

# 프리미엄 다크/그레이 톤 스타일링을 위한 마크다운 CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 주식 투자 전략 시뮬레이터 및 백테스트 대시보드")
st.write("머신러닝 롤링 예측 전략과 래리 윌리엄스 변동성 돌파 전략의 성과를 분석하는 인터랙티브 대시보드입니다.")

# 세션 상태 초기화 및 관리
if 'run_backtest' not in st.session_state:
    st.session_state['run_backtest'] = False

# 사이드바 설정
st.sidebar.header("⚙️ 전략 및 파라미터 설정")

# 1. 라디오 버튼을 사용하여 전략 및 통합 모드 선택 (3개 옵션 제공)
strategy_choice = st.sidebar.radio(
    "💡 분석할 전략 선택",
    options=["머신러닝 롤링 예측 전략", "변동성 돌파 전략 (Larry Williams)", "두 전략 통합 비교"]
)

# 2. 공통 종목 코드 입력
ticker_code = st.sidebar.text_input("종목 코드 입력 (예: 360750, 453850, TLT)", "360750")
ticker_symbol = ticker_code.strip().upper()
ticker_name = get_ticker_name(ticker_code)
is_known_ticker = ticker_name != UNKNOWN_TICKER_NAME
if is_known_ticker:
    st.sidebar.info(f"선택된 종목: **{ticker_name}** ({ticker_symbol})")
else:
    hint = INVALID_TICKER_HINTS.get(ticker_symbol, "")
    st.sidebar.warning(f"알 수 없는 종목 코드입니다: **{ticker_symbol or '미입력'}**")
    if hint:
        st.sidebar.info(hint)

# 🚀 백테스트 실행 버튼 위치를 상단(종목 코드 바로 아래, 시작 날짜 위)으로 이동
run_button_clicked = st.sidebar.button("🚀 백테스트 실행하기", use_container_width=True)
if run_button_clicked:
    st.session_state['run_backtest'] = True

# 3. 공통 기간 설정 (종료 날짜 기본값을 실행 당일 오늘 날짜로 동적 자동 입력)
start_date = st.sidebar.text_input("시작 날짜 (YYYYMMDD)", "20240101")
today_str = datetime.today().strftime('%Y%m%d')
end_date = st.sidebar.text_input("종료 날짜 (YYYYMMDD)", today_str)

# 4. 실전 투자 조건 설정 (사용자가 쉼표 없이 숫자만 편리하게 타이핑하여 입력하도록 원복)
st.sidebar.subheader("💸 실전 투자 조건 (거래비용)")
initial_budget = st.sidebar.number_input("💵 초기 투자 원금 (원)", min_value=100000, value=10000000, step=1000000, format="%d")

fee_rate = st.sidebar.number_input("💸 거래 수수료율 (편도, %)", min_value=0.0, max_value=1.0, value=0.015, step=0.005, format="%.3f")
slippage_rate = st.sidebar.number_input("📉 슬리피지율 (편도, %)", min_value=0.0, max_value=1.0, value=0.02, step=0.01, format="%.2f")

# 5. 전략별 개별 설정
st.sidebar.subheader("🎯 전략 파라미터")
if strategy_choice == "머신러닝 롤링 예측 전략":
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = 0.5 # 미사용 기본값
elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    window_size = 90 # 미사용 기본값
else:
    # 통합 비교 모드 시 두 설정 모두 표시
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)

# --- 세션 상태 초기화 및 관리 ---
if 'stock_data' not in st.session_state:
    st.session_state['stock_data'] = pd.DataFrame()
if 'loaded_ticker' not in st.session_state:
    st.session_state['loaded_ticker'] = ""
if 'loaded_start' not in st.session_state:
    st.session_state['loaded_start'] = ""
if 'loaded_end' not in st.session_state:
    st.session_state['loaded_end'] = ""

# 입력된 종목코드나 기간이 이미 세션에 로드된 것과 일치하는지 판별
is_data_cached = (
    not st.session_state['stock_data'].empty and
    st.session_state['loaded_ticker'] == ticker_code.strip() and
    st.session_state['loaded_start'] == start_date and
    st.session_state['loaded_end'] == end_date
)

# 데이터 로딩 로직 최적화: 종목이나 기간이 바뀐 최초 1회에만 데이터 로드 스피너가 작동
if not is_known_ticker:
    st.session_state['stock_data'] = pd.DataFrame()
    st.session_state['loaded_ticker'] = ""
    st.session_state['loaded_start'] = ""
    st.session_state['loaded_end'] = ""
    st.session_state['run_backtest'] = False
elif not is_data_cached:
    with st.spinner(f"📡 {ticker_name} ({ticker_symbol}) 주식 데이터를 불러오는 중..."):
        df = load_data(start_date, end_date, ticker_code)
        if not df.empty:
            st.session_state['stock_data'] = df
            st.session_state['loaded_ticker'] = ticker_code.strip()
            st.session_state['loaded_start'] = start_date
            st.session_state['loaded_end'] = end_date
            # 종목이나 날짜만 바뀐 경우에는 이전 실행 상태를 리셋하되,
            # 이번 rerun에서 버튼을 누른 경우에는 즉시 백테스트가 이어지도록 유지
            if not run_button_clicked:
                st.session_state['run_backtest'] = False
        else:
            st.session_state['stock_data'] = pd.DataFrame()

df = st.session_state['stock_data']

# 백테스트 연산 및 시각화 출력 (데이터가 성공적으로 있는 경우에만 기동)
if not df.empty:
    if st.session_state.get('run_backtest', False):
        # 1. 1차 검증
        if strategy_choice in ["머신러닝 롤링 예측 전략", "두 전략 통합 비교"] and len(df) <= window_size:
            st.error(f"데이터의 총 크기({len(df)}일)가 학습 윈도우 크기({window_size}일)보다 작습니다. 기간을 늘려주세요.")
        else:
            # --- 백테스트 연산 수행 ---
            
            # 머신러닝 모드 연산
            if strategy_choice == "머신러닝 롤링 예측 전략":
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size)
                actual_close = df['종가'].loc[pred_series.index]
                ml_df = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate)
                
                # 평가 지표
                mae = (actual_close - pred_series).abs().mean()
                mape = ((actual_close - pred_series).abs() / actual_close).mean() * 100
                strategy_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                total_days = len(pred_series)
                
            # 변동성 돌파 모드 연산
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                vbt_df = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate)
                strategy_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = vbt_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = vbt_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(vbt_df['Buy_Signal'])
                total_days = len(vbt_df)
                
            # 통합 비교 모드 연산 (두 개 모두 연산)
            else:
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size)
                actual_close = df['종가'].loc[pred_series.index]
                ml_df = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate)
                
                # 변동성 돌파도 머신러닝 예측 기간과 정확히 일치시켜 1대1 비교
                vbt_full = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate)
                vbt_df = vbt_full.loc[pred_series.index]
                
                ml_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                vbt_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                
                ml_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                vbt_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                mae = (actual_close - pred_series).abs().mean()
                
            # --- 구조 1: 성과 지표 (Metrics 4개) ---
            col1, col2, col3, col4 = st.columns(4)
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                with col1:
                    st.metric(label="🤖 머신러닝 최종 잔고 (수익률)", value=f"{strategy_final_balance:,.0f} 원", delta=f"{strategy_final_return:+.2f}%")
                with col2:
                    st.metric(label="📈 단순 보유 최종 잔고 (수익률)", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col3:
                    st.metric(label="📊 평균 절대 오차 (MAE)", value=f"{mae:,.0f} 원", delta=f"오차율(MAPE): {mape:.2f}%", delta_color="inverse")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")
                    
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                with col1:
                    st.metric(label="⚡ 변동성 돌파 최종 잔고 (수익률)", value=f"{strategy_final_balance:,.0f} 원", delta=f"{strategy_final_return:+.2f}%")
                with col2:
                    st.metric(label="📈 단순 보유 최종 잔고 (수익률)", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col3:
                    st.metric(label="🛒 총 매수 체결 횟수", value=f"{total_buys} 회", delta=f"체결률: {(total_buys/total_days)*100:.1f}%")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")
                    
            else: # 통합 비교 모드
                with col1:
                    st.metric(label="🤖 머신러닝 최종 잔고", value=f"{ml_final_balance:,.0f} 원", delta=f"{ml_final_return:+.2f}%")
                with col2:
                    st.metric(label="⚡ 변동성 돌파 최종 잔고", value=f"{vbt_final_balance:,.0f} 원", delta=f"{vbt_final_return:+.2f}%")
                with col3:
                    st.metric(label="📈 단순 보유 최종 잔고", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{len(ml_df)} 일")

            # --- 구조 2: 주가 비교 차트 ---
            if strategy_choice == "머신러닝 롤링 예측 전략":
                st.subheader(f"🔮 실제 {ticker_name} 종가 vs 예측 주가 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                st.subheader(f"🏷️ 실제 {ticker_name} 주가 vs 매수 목표가(Buy Target)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="매수 목표가 (시가 + Range * K)", 
                    line=dict(color="#d62728", width=1.5, dash="dash"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
                
            else: # 통합 비교 모드
                st.subheader(f"📊 실제 {ticker_name} 주가 및 전략별 신호선 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="돌파 매수 목표가 (VBT)", 
                    line=dict(color="#d62728", width=1.5, dash="dot"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
            
            fig_price.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                height=400
            )
            st.plotly_chart(fig_price, use_container_width=True)

            # --- 구조 3: 누적 수익률 비교 추이 그래프 ---
            st.subheader("📈 백테스트 누적 수익률 비교 추이")
            fig_ret = go.Figure()
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Strategy_Cum_Return'], name="🤖 머신러닝 예측 전략", 
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>머신러닝 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Strategy_Cum_Return'], name="⚡ 변동성 돌파 전략", 
                    line=dict(color="#9467bd", width=2.5),
                    hovertemplate='<b>변동성 돌파 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            else: # 통합 비교 모드
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Strategy_Cum_Return'], name="🤖 머신러닝 예측 전략", 
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>머신러닝 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Strategy_Cum_Return'], name="⚡ 변동성 돌파 전략", 
                    line=dict(color="#9467bd", width=2.5),
                    hovertemplate='<b>변동성 돌파 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Hold_Cum_Return'], name="📈 단순 보유 (Buy & Hold)", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                
            fig_ret.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="누적 수익률 (%)"),
                height=400
            )
            st.plotly_chart(fig_ret, use_container_width=True)

            # --- 구조 4: 월별 분석 차트 및 통계 테이블 (2열 분할 구성) ---
            st.subheader("📅 상세 요약 및 월별 분석")
            
            col_chart, col_table = st.columns([2, 1])
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                monthly_stats = calculate_ml_monthly_stats(actual_close, pred_series, ml_df)
                with col_chart:
                    fig_bar = px.bar(
                        monthly_stats, x='년-월', y='평균 절대 오차 (원)', 
                        color='평균 절대 오차 (원)',
                        color_continuous_scale=px.colors.sequential.OrRd
                    )
                    fig_bar.update_traces(hovertemplate='<b>년-월</b>: %{x}<br><b>평균 절대 오차</b>: %{y:,.0f}원<extra></extra>')
                    fig_bar.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(type='category', title="년-월"),
                        yaxis=dict(tickformat=",", title="평균 오차 (원)"),
                        coloraxis_colorbar=dict(title="오차 (원)"),
                        height=350
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📊 **월별 통계 요약 데이터**")
                    display_df = monthly_stats.copy()
                    display_df['평균 절대 오차 (원)'] = display_df['평균 절대 오차 (원)'].map('{:,.0f}원'.format)
                    display_df['평균 오차율 (%)'] = display_df['평균 오차율 (%)'].map('{:.2f}%'.format)
                    display_df['월간 수익률 (%)'] = display_df['월간 수익률 (%)'].map('{:+.2f}%'.format)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                summary_stats = calculate_vbt_monthly_stats(vbt_df)
                with col_chart:
                    fig_bar = px.bar(
                        vbt_df, x=vbt_df.index, y='Daily_Return_Pct',
                        color='Daily_Return_Pct',
                        color_continuous_scale=px.colors.diverging.RdYlGn,
                        color_continuous_midpoint=0.0
                    )
                    fig_bar.update_traces(hovertemplate='<b>날짜</b>: %{x}<br><b>일별 수익률</b>: %{y:.2f}%<extra></extra>')
                    fig_bar.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(title="날짜"),
                        yaxis=dict(title="일별 수익률 (%)"),
                        coloraxis_colorbar=dict(title="수익률 (%)"),
                        height=350
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📅 **월별 거래 요약 데이터**")
                    display_stats = summary_stats.copy()
                    display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    display_stats['전략 수익률 (%)'] = display_stats['전략 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['단순 보유 수익률 (%)'] = display_stats['단순 보유 수익률 (%)'].map('{:+.2f}%'.format)
                    st.dataframe(display_stats, use_container_width=True, hide_index=True)
                    
            else: # 통합 비교 모드
                combined_stats = calculate_combined_monthly_stats(ml_df, vbt_df)
                with col_chart:
                    fig_monthly_bar = go.Figure()
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['머신러닝 수익률 (%)'],
                        name="🤖 머신러닝", marker_color="#2ca02c",
                        hovertemplate='<b>머신러닝 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['변동성 돌파 수익률 (%)'],
                        name="⚡ 변동성 돌파", marker_color="#9467bd",
                        hovertemplate='<b>변동성 돌파 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['단순 보유 수익률 (%)'],
                        name="📈 단순 보유", marker_color="#7f7f7f",
                        hovertemplate='<b>단순 보유 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.update_layout(
                        barmode='group', plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(type='category', title="년-월"),
                        yaxis=dict(title="월간 수익률 (%)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=350
                    )
                    st.plotly_chart(fig_monthly_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📊 **월별 전략별 수익률 대조 테이블**")
                    display_stats = combined_stats.copy()
                    display_stats['머신러닝 수익률 (%)'] = display_stats['머신러닝 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['변동성 돌파 수익률 (%)'] = display_stats['변동성 돌파 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['단순 보유 수익률 (%)'] = display_stats['단순 보유 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['돌파 매수 횟수 (회)'] = display_stats['돌파 매수 횟수 (회)'].map('{:,.0f}회'.format)
                    display_stats['머신러닝 오차 (원)'] = display_stats['머신러닝 오차 (원)'].map('{:,.0f}원'.format)
                    st.dataframe(display_stats, use_container_width=True, hide_index=True)
    else:
        st.info("👈 왼쪽 사이드바에서 [백테스트 실행하기] 버튼을 눌러주세요!")
else:
    if not is_known_ticker:
        hint = INVALID_TICKER_HINTS.get(ticker_symbol, "")
        message = "알 수 없는 종목 코드입니다. 거래소에 등록된 종목 코드나 티커를 입력해 주세요."
        if hint:
            message = f"{message} {hint}"
        st.error(message)
    else:
        st.info("👈 왼쪽 사이드바에서 전략 및 조건을 설정한 후 [백테스트 실행하기] 버튼을 눌러주세요!")
