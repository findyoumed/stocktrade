import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# [LOG: 20260604_1208]

# 1. 데이터 불러오기 함수
@st.cache_data
def load_data(start_date, end_date):
    """삼성전자 주식 데이터를 불러옵니다."""
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, "005930")
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# 2. 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['고가'].iloc[1:]
    return X, y

# 3. 롤링 윈도우 예측 수행 함수
def run_rolling_forecast(X, y, df_index, window_size):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 고가를 예측합니다."""
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

# 4. 월별 백테스트 통계 계산 함수
def calculate_monthly_stats(actual, predicted):
    """실제 값과 예측 값을 비교하여 월별 평균 절대 오차(MAE)를 계산합니다."""
    compare_df = pd.DataFrame({
        'Actual': actual,
        'Predicted': predicted
    }).dropna()
    
    # 절대 오차 계산
    compare_df['Absolute Error'] = (compare_df['Actual'] - compare_df['Predicted']).abs()
    
    # 월별 그룹화 (YYYY-MM 형식)
    compare_df['YearMonth'] = compare_df.index.strftime('%Y-%m')
    
    # 월별 MAE 계산
    monthly_mae = compare_df.groupby('YearMonth')['Absolute Error'].mean().reset_index()
    monthly_mae.columns = ['YearMonth', 'Average Error (Won)']
    
    # 오차율(%) 계산 (실제값 대비 오차 비율)
    compare_df['Error Rate (%)'] = (compare_df['Absolute Error'] / compare_df['Actual']) * 100
    monthly_error_rate = compare_df.groupby('YearMonth')['Error Rate (%)'].mean().reset_index()
    
    stats_df = pd.merge(monthly_mae, monthly_error_rate, on='YearMonth')
    return stats_df

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="삼성전자 주가 예측 대시보드", layout="wide")

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

st.title("📈 삼성전자 주가 머신러닝 예측 및 월별 백테스트")
st.write("작성된 랜덤 포레스트 롤링 예측 모델을 기반으로 시각화한 프리미엄 대시보드입니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 예측 설정")
start_date = st.sidebar.text_input("시작 날짜 (YYYYMMDD)", "20250101")
end_date = st.sidebar.text_input("종료 날짜 (YYYYMMDD)", "20260531")
window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)

if st.sidebar.button("🚀 예측 실행하기", use_container_width=True):
    with st.spinner("KRX 주가 데이터 로딩 및 머신러닝 학습 중..."):
        # 데이터 로드 및 검증
        df = load_data(start_date, end_date)
        
        if not df.empty and len(df) > window_size:
            X, y = prepare_features(df)
            
            # 예측 수행
            pred_series = run_rolling_forecast(X, y, df.index, window_size)
            
            # 전체 비교용 데이터프레임
            actual_high = df['고가'].loc[pred_series.index]
            
            # 1. 상단 성과 지표 (Metrics)
            mae = (actual_high - pred_series).abs().mean()
            mape = ((actual_high - pred_series).abs() / actual_high).mean() * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="📊 전체 평균 절대 오차 (MAE)", value=f"{mae:,.0f} 원")
            with col2:
                st.metric(label="🎯 평균 절대 백분율 오차 (MAPE)", value=f"{mape:.2f} %")
            with col3:
                st.metric(label="⏳ 총 예측 영업일 수", value=f"{len(pred_series)} 일")
            
            # 2. 메인 예측 차트 (Plotly)
            st.subheader("🔮 실제 주가(고가) vs 예측 주가")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['고가'], name="Actual High (실제 고가)", line=dict(color="#1f77b4", width=2)))
            fig.add_trace(go.Scatter(x=pred_series.index, y=pred_series, name="Predicted High (예측 고가)", line=dict(color="#ff7f0e", width=2, dash="dash")))
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=","),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. 월별 백테스트 결과 및 차트
            st.subheader("📅 월별 백테스트 예측 성능 (평균 오차)")
            monthly_stats = calculate_monthly_stats(actual_high, pred_series)
            
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                # 월별 평균 오차(원) 바 차트
                fig_bar = px.bar(
                    monthly_stats, 
                    x='YearMonth', 
                    y='Average Error (Won)', 
                    labels={'YearMonth': '년-월', 'Average Error (Won)': '평균 절대 오차 (원)'},
                    color='Average Error (Won)',
                    color_continuous_scale=px.colors.sequential.OrRd
                )
                fig_bar.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(type='category'),
                    yaxis=dict(tickformat=","),
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col_table:
                # 월별 통계 테이블 표기
                st.write("📊 **월별 통계 상세 데이터**")
                display_df = monthly_stats.copy()
                display_df['Average Error (Won)'] = display_df['Average Error (Won)'].map('{:,.0f}원'.format)
                display_df['Error Rate (%)'] = display_df['Error Rate (%)'].map('{:.2f}%'.format)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
        else:
            st.warning("데이터가 부족하거나 불러오지 못했습니다. 날짜 범위 또는 윈도우 크기를 다시 설정해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 예측 기간 및 설정을 확인하고 [예측 실행하기] 버튼을 눌러주세요!")
