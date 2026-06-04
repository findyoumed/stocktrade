import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# [LOG: 20260604_1241]

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

# 3. 머신러닝 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

# 4. 머신러닝 롤링 윈도우 예측 수행 함수
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

# 5. 머신러닝 백테스트 수익률 계산 함수
def run_ml_backtest(df, pred_series):
    """예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다."""
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
    
    # 누적 수익률 계산 (%)
    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    
    return backtest_df

# 6. 머신러닝 월별 백테스트 통계 계산 함수
def calculate_ml_monthly_stats(actual, predicted, backtest_df):
    """실제 값과 예측 값을 비교하여 머신러닝 예측 오차 및 월별 수익률 통계를 계산합니다."""
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

# 7. 변동성 돌파 전략 백테스트 계산 함수
def run_vbt_backtest(df, K):
    """변동성 돌파 전략 백테스트를 수행합니다."""
    vbt_df = df.copy()
    
    # 변동성 폭 계산 (전일 고가 - 전일 저가)
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    
    # 매수 목표가 계산 (당일 시가 + 변동폭 * K)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    
    # 매수 조건: 당일 고가가 매수 목표가를 초과했는지 판별
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    # 전략 일별 수익률 계산 (매수 체결 시 당일 종가 / 매수 목표가, 미체결 시 1.0)
    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        vbt_df['종가'] / vbt_df['Buy_Target'],
        1.0
    )
    
    # 단순 보유(Buy & Hold) 일별 수익률
    vbt_df['Hold_Return'] = vbt_df['종가'] / vbt_df['종가'].shift(1)
    vbt_df['Hold_Return'] = vbt_df['Hold_Return'].fillna(1.0)
    
    # 누적 수익률 계산 (%)
    vbt_df['Strategy_Cum_Return'] = (vbt_df['Strategy_Return'].cumprod() - 1) * 100
    vbt_df['Hold_Cum_Return'] = (vbt_df['Hold_Return'].cumprod() - 1) * 100
    
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

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="주식 백테스트 및 예측 대시보드", layout="wide")

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
st.write("머신러닝 롤링 예측 및 래리 윌리엄스 변동성 돌파 전략의 성과를 분석하는 인터랙티브 대시보드입니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 전략 및 파라미터 설정")

# 1. 라디오 버튼을 사용한 전략 선택
strategy_choice = st.sidebar.radio(
    "💡 분석할 전략 선택",
    options=["머신러닝 롤링 예측 전략", "변동성 돌파 전략 (Larry Williams)"]
)

# 2. 공통 종목 코드 입력
ticker_code = st.sidebar.text_input("종목 코드 입력 (6자리)", "005930")
ticker_name = get_ticker_name(ticker_code)
st.sidebar.info(f"선택된 종목: **{ticker_name}** ({ticker_code})")

# 3. 공통 기간 설정
start_date = st.sidebar.text_input("시작 날짜 (YYYYMMDD)", "20250101")
end_date = st.sidebar.text_input("종료 날짜 (YYYYMMDD)", "20260531")

# 4. 전략별 개별 설정
if strategy_choice == "머신러닝 롤링 예측 전략":
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = 0.5 # 미사용 기본값
else:
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    window_size = 90 # 미사용 기본값

# 실행 버튼
if st.sidebar.button("🚀 백테스트 실행하기", use_container_width=True):
    with st.spinner(f"{ticker_name} 주식 데이터를 불러오는 중..."):
        df = load_data(start_date, end_date, ticker_code)
        
        if df.empty:
            st.warning("데이터가 부족하거나 불러오지 못했습니다. 날짜 범위 또는 종목 코드를 다시 설정해 주세요.")
        else:
            if strategy_choice == "머신러닝 롤링 예측 전략":
                if len(df) <= window_size:
                    st.error(f"데이터의 총 크기({len(df)}일)가 학습 윈도우 크기({window_size}일)보다 작습니다. 기간을 늘려주세요.")
                else:
                    X, y = prepare_features(df)
                    
                    # 롤링 예측 및 백테스트 실행
                    pred_series = run_rolling_forecast(X, y, df.index, window_size)
                    actual_close = df['종가'].loc[pred_series.index]
                    backtest_df = run_ml_backtest(df, pred_series)
                    
                    # 지표 계산
                    mae = (actual_close - pred_series).abs().mean()
                    mape = ((actual_close - pred_series).abs() / actual_close).mean() * 100
                    strategy_final_return = backtest_df['Strategy_Cum_Return'].iloc[-1]
                    hold_final_return = backtest_df['Hold_Cum_Return'].iloc[-1]
                    
                    # 성과 지표 출력
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(label="📊 평균 절대 오차", value=f"{mae:,.0f} 원")
                    with col2:
                        st.metric(label="🎯 평균 백분율 오차 (MAPE)", value=f"{mape:.2f} %")
                    with col3:
                        st.metric(
                            label="💰 전략 누적 수익률", 
                            value=f"{strategy_final_return:.2f} %",
                            delta=f"단순보유({hold_final_return:.2f}%) 대비: {strategy_final_return - hold_final_return:+.2f}%"
                        )
                    with col4:
                        st.metric(label="⏳ 총 분석 영업일 수", value=f"{len(pred_series)} 일")
                    
                    # 실제 vs 예측 비교 차트
                    st.subheader(f"🔮 실제 {ticker_name} 종가 vs 예측 주가 비교")
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
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 누적 수익률 추이 그래프
                    st.subheader("📈 백테스트 누적 수익률 비교 추이")
                    fig_ret = go.Figure()
                    fig_ret.add_trace(go.Scatter(
                        x=backtest_df.index, 
                        y=backtest_df['Strategy_Cum_Return'], 
                        name="머신러닝 롤링 예측 전략", 
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
                    
                    # 월별 통계 분석
                    st.subheader(f"📅 월별 예측 오차 및 수익률 분석 요약")
                    monthly_stats = calculate_ml_monthly_stats(actual_close, pred_series, backtest_df)
                    
                    col_chart, col_table = st.columns([2, 1])
                    with col_chart:
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
            
            else:
                # 변동성 돌파 전략 실행
                vbt_df = run_vbt_backtest(df, K)
                summary_stats = calculate_vbt_monthly_stats(vbt_df)
                
                strategy_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = vbt_df['Hold_Cum_Return'].iloc[-1]
                total_buys = np.sum(vbt_df['Buy_Signal'])
                total_days = len(vbt_df)
                
                # 성과 지표 출력
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label="💰 전략 최종 누적 수익률", value=f"{strategy_final_return:.2f} %")
                with col2:
                    st.metric(label="📈 단순 보유 최종 누적 수익률", value=f"{hold_final_return:.2f} %")
                with col3:
                    st.metric(
                        label="🛒 총 매수 체결 횟수", 
                        value=f"{total_buys} 회",
                        delta=f"체결률: {(total_buys/total_days)*100:.1f} %"
                    )
                with col4:
                    st.metric(label="⏳ 총 영업일 수", value=f"{total_days} 일")
                
                # 실제 주가 vs 매수 목표가 비교 차트
                st.subheader(f"🏷️ 실제 {ticker_name} 주가 vs 매수 목표가(Buy Target)")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=vbt_df.index, 
                    y=vbt_df['종가'], 
                    name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig.add_trace(go.Scatter(
                    x=vbt_df.index, 
                    y=vbt_df['Buy_Target'], 
                    name="매수 목표가 (시가 + Range * K)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가 (원)"),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 누적 수익률 비교 추이
                st.subheader("📈 백테스트 누적 수익률 비교 추이")
                fig_ret = go.Figure()
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, 
                    y=vbt_df['Strategy_Cum_Return'], 
                    name="변동성 돌파 전략", 
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>변동성 돌파 수익률</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, 
                    y=vbt_df['Hold_Cum_Return'], 
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
                
                # 일별 수익률 변동 바 차트 및 요약 테이블
                st.subheader("📊 변동성 돌파 전략 일별 수익률 및 월별 통계")
                
                col_chart, col_table = st.columns([2, 1])
                with col_chart:
                    # 일별 수익률 막대 차트 (변동성 돌파 전략_일별수익률.py의 시각화 로직 통합)
                    fig_bar = px.bar(
                        vbt_df, 
                        x=vbt_df.index, 
                        y='Daily_Return_Pct',
                        labels={'Daily_Return_Pct': '일별 수익률 (%)'},
                        color='Daily_Return_Pct',
                        color_continuous_scale=px.colors.diverging.RdYlGn,
                        color_continuous_midpoint=0.0
                    )
                    fig_bar.update_traces(
                        hovertemplate='<b>날짜</b>: %{x}<br><b>일별 수익률</b>: %{y:.2f}%<extra></extra>'
                    )
                    fig_bar.update_layout(
                        plot_bgcolor="white",
                        paper_bgcolor="white",
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
                    
else:
    st.info("👈 왼쪽 사이드바에서 전략 및 조건을 설정한 후 [백테스트 실행하기] 버튼을 눌러주세요!")
