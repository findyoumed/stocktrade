import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# [LOG: 20260604_1212]

# 1. 종목 이름 조회 함수
@st.cache_data
def get_ticker_name(ticker_code):
    """종목 코드를 받아 종목명을 반환합니다. (예: 005930 -> 삼성전자)"""
    try:
        name = stock.get_market_ticker_name(ticker_code)
        if name == "":
            return "알 수 없는 종목"
        return name
    except Exception:
        return "알 수 없는 종목"

# 2. 주식 데이터 불러오기 함수
@st.cache_data
def load_data(start_date, end_date, ticker_code):
    """선택한 종목의 주식 데이터를 불러옵니다."""
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker_code)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# 3. 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

# 4. 롤링 윈도우 예측 수행 함수
def run_rolling_forecast(X, y, df_index, window_size):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 종가를 예측합니다."""
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
        status_text.text(f"예측 진행 중: {current_step}/{total_steps} 영업일 완료...")
        
    progress_bar.empty()
    status_text.empty()
    
    pred_series = pd.Series(predictions, index=prediction_dates)
    return pred_series

# 5. 백테스트 수익률 계산 함수
def run_backtest(df, pred_series):
    """예측 결과를 기반으로 백테스트 수익률을 시뮬레이션합니다."""
    backtest_df = pd.DataFrame({
        'Actual_Close': df['종가'].loc[pred_series.index],
        'Predicted_Close': pred_series,
        'Prev_Close': df['종가'].shift(1).loc[pred_series.index]
    }).dropna()
    
    # 매수 신호: 내일 종가 예측치 > 오늘 실제 종가 일 때 매수
    backtest_df['Buy_Signal'] = backtest_df['Predicted_Close'] > backtest_df['Prev_Close']
    
    # 전략 일별 수익률 계산 (매수 시 당일 실제 종가 / 전일 실제 종가, 미매수 시 1.0)
    backtest_df['Strategy_Return'] = np.where(
        backtest_df['Buy_Signal'],
        backtest_df['Actual_Close'] / backtest_df['Prev_Close'],
        1.0
    )
    
    # 단순 보유(Buy & Hold) 일별 수익률
    backtest_df['Hold_Return'] = backtest_df['Actual_Close'] / backtest_df['Prev_Close']
    
    # 누적 수익률 계산
    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    
    return backtest_df

# 6. 월별 백테스트 통계 계산 함수 (컬럼 한글화)
def calculate_monthly_stats(actual, predicted, backtest_df):
    """실제 값과 예측 값을 비교하여 월별 통계를 계산합니다. 영문 키를 배제하여 한글로 변환합니다."""
    compare_df = pd.DataFrame({
        'Actual': actual,
        'Predicted': predicted,
        'Strategy_Return': backtest_df['Strategy_Return']
    }).dropna()
    
    # 절대 오차 계산
    compare_df['Absolute Error'] = (compare_df['Actual'] - compare_df['Predicted']).abs()
    
    # 월별 그룹화 (YYYY-MM 형식)
    compare_df['YearMonth'] = compare_df.index.strftime('%Y-%m')
    
    # 월별 MAE 계산
    monthly_mae = compare_df.groupby('YearMonth')['Absolute Error'].mean().reset_index()
    monthly_mae.columns = ['년-월', '평균 절대 오차 (원)']
    
    # 오차율(%) 계산 (실제값 대비 오차 비율)
    compare_df['Error Rate (%)'] = (compare_df['Absolute Error'] / compare_df['Actual']) * 100
    monthly_error_rate = compare_df.groupby('YearMonth')['Error Rate (%)'].mean().reset_index()
    monthly_error_rate.columns = ['년-월', '평균 오차율 (%)']
    
    # 월별 누적 수익률 계산
    monthly_return = compare_df.groupby('YearMonth')['Strategy_Return'].prod().reset_index()
    monthly_return['Strategy_Return'] = (monthly_return['Strategy_Return'] - 1) * 100
    monthly_return.columns = ['년-월', '월간 수익률 (%)']
    
    stats_df = pd.merge(monthly_mae, monthly_error_rate, on='년-월')
    stats_df = pd.merge(stats_df, monthly_return, on='년-월')
    return stats_df

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="주가 예측 및 백테스트 대시보드", layout="wide")

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

st.title("📈 주가 머신러닝 예측 및 월별 백테스트 대시보드")
st.write("작성된 랜덤 포레스트 롤링 예측 모델을 기반으로 시각화한 프리미엄 대시보드입니다. (종가 예측 기반)")

# 사이드바 설정
st.sidebar.header("⚙️ 예측 설정")

# 종목 코드 입력 및 자동 이름 조회
ticker_code = st.sidebar.text_input("종목 코드 입력 (6자리)", "005930")
ticker_name = get_ticker_name(ticker_code)
st.sidebar.info(f"선택된 종목: **{ticker_name}** ({ticker_code})")

# 기간 설정
start_date = st.sidebar.text_input("시작 날짜 (YYYYMMDD)", "20250101")
end_date = st.sidebar.text_input("종료 날짜 (YYYYMMDD)", "20260531")

# 학습 윈도이어 슬라이더
window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)

if st.sidebar.button("🚀 예측 실행하기", use_container_width=True):
    with st.spinner(f"{ticker_name} 주가 데이터를 불러와 머신러닝 학습 중..."):
        # 데이터 로드
        df = load_data(start_date, end_date, ticker_code)
        
        if not df.empty and len(df) > window_size:
            X, y = prepare_features(df)
            
            # 예측 수행
            pred_series = run_rolling_forecast(X, y, df.index, window_size)
            
            # 실제 종가 데이터 추출
            actual_close = df['종가'].loc[pred_series.index]
            
            # 백테스트 수행
            backtest_df = run_backtest(df, pred_series)
            
            # 1. 상단 성과 지표 (Metrics 한글화)
            mae = (actual_close - pred_series).abs().mean()
            mape = ((actual_close - pred_series).abs() / actual_close).mean() * 100
            strategy_final_return = backtest_df['Strategy_Cum_Return'].iloc[-1]
            hold_final_return = backtest_df['Hold_Cum_Return'].iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="📊 전체 평균 절대 오차", value=f"{mae:,.0f} 원")
            with col2:
                st.metric(label="🎯 평균 절대 백분율 오차", value=f"{mape:.2f} %")
            with col3:
                st.metric(
                    label="💰 머신러닝 전략 누적 수익률", 
                    value=f"{strategy_final_return:.2f} %",
                    delta=f"단순보유({hold_final_return:.2f}%) 대비 차이: {strategy_final_return - hold_final_return:.2f}%"
                )
            with col4:
                st.metric(label="⏳ 총 예측 영업일 수", value=f"{len(pred_series)} 일")
            
            # 2. 메인 예측 차트 (Plotly 호버 및 범례 한글화)
            st.subheader(f"🔮 실제 {ticker_name} 주가(종가) vs 예측 주가 비교")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df['종가'], 
                name="실제 종가", 
                line=dict(color="#1f77b4", width=2),
                hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=pred_series.index, 
                y=pred_series, 
                name="예측 종가 (머신러닝)", 
                line=dict(color="#ff7f0e", width=2, dash="dash"),
                hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
            ))
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가 (원)"),
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. 누적 수익률 추이 그래프 (Plotly 호버 및 범례 한글화)
            st.subheader("📈 백테스트 누적 수익률 비교 추이")
            fig_ret = go.Figure()
            fig_ret.add_trace(go.Scatter(
                x=backtest_df.index, 
                y=backtest_df['Strategy_Cum_Return'], 
                name="머신러닝 예측 매매 전략", 
                line=dict(color="#2ca02c", width=2.5),
                hovertemplate='<b>머신러닝 전략 수익률</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
            ))
            fig_ret.add_trace(go.Scatter(
                x=backtest_df.index, 
                y=backtest_df['Hold_Cum_Return'], 
                name="단순 보유", 
                line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                hovertemplate='<b>단순 보유 수익률</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
            ))
            fig_ret.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="누적 수익률 (%)"),
                height=400
            )
            st.plotly_chart(fig_ret, use_container_width=True)
            
            # 4. 월별 백테스트 결과 및 차트
            st.subheader(f"📅 월별 백테스트 예측 오차 및 수익률 분석")
            monthly_stats = calculate_monthly_stats(actual_close, pred_series, backtest_df)
            
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                # 월별 평균 오차(원) 바 차트 (호버 툴팁 완전 한글화)
                fig_bar = px.bar(
                    monthly_stats, 
                    x='년-월', 
                    y='평균 절대 오차 (원)', 
                    color='평균 절대 오차 (원)',
                    color_continuous_scale=px.colors.sequential.OrRd
                )
                fig_bar.update_traces(
                    hovertemplate='<b>년-월</b>: %{x}<br><b>평균 절대 오차</b>: %{y:,.0f}원<extra></extra>'
                )
                fig_bar.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(type='category', title="년-월"),
                    yaxis=dict(tickformat=",", title="평균 오차 (원)"),
                    coloraxis_colorbar=dict(title="평균 오차 (원)"),
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col_table:
                # 월별 통계 테이블 표기
                st.write("📊 **월별 백테스트 요약 데이터**")
                display_df = monthly_stats.copy()
                display_df['평균 절대 오차 (원)'] = display_df['평균 절대 오차 (원)'].map('{:,.0f}원'.format)
                display_df['평균 오차율 (%)'] = display_df['평균 오차율 (%)'].map('{:.2f}%'.format)
                display_df['월간 수익률 (%)'] = display_df['월간 수익률 (%)'].map('{:+.2f}%'.format)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
        else:
            st.warning("데이터가 부족하거나 불러오지 못했습니다. 날짜 범위 또는 윈도우 크기를 다시 설정해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 종목 코드, 기간을 설정한 후 [예측 실행하기] 버튼을 눌러주세요!")
