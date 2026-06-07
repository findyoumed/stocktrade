import sys
import subprocess
from pathlib import Path

# 1. Reset dashboard file to clean head state
subprocess.run(["git", "checkout", "chapter3/stock_prediction_dashboard.py"])
print("Restored clean dashboard file.")

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# Normalize to LF
content_lf = content.replace("\r\n", "\n")

# 1. Imports
target_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
)"""

replacement_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
    run_dca_backtest,
    calculate_dca_monthly_stats,
)"""

# 2. strategy_choice selectbox options
target_selectbox = """        "이동평균선 골든크로스 전략",
        "RSI 과매도 반등 전략",
        "볼린저 밴드 반등 전략",
        "MACD 추세 전략",
        "스토캐스틱 오실레이터 전략\","""

replacement_selectbox = """        "이동평균선 골든크로스 전략",
        "RSI 과매도 반등 전략",
        "볼린저 밴드 반등 전략",
        "MACD 추세 전략",
        "200일선 + MACD 추세 필터 전략",
        "적립식 존버 물타기 (DCA) 전략",
        "스토캐스틱 오실레이터 전략\","""

# 3. Sidebar parameter defaults
target_defaults = """dm_lookback_days = 252
dm_defense_ticker = "IEF"
dm_defensive_mode = "방어자산"
if strategy_choice == "머신러닝 롤링 예측 전략":"""

replacement_defaults = """dm_lookback_days = 252
dm_defense_ticker = "IEF"
dm_defensive_mode = "방어자산"
sma_macd_sma = 200
sma_macd_fast = 12
sma_macd_slow = 26
sma_macd_signal = 9
sma_macd_defense_ticker = "TLT"
sma_macd_defensive_mode = "방어자산"
sma_macd_signal_mode = "sma_exit"
sma_macd_rebalance_frequency = "M"
if strategy_choice == "머신러닝 롤링 예측 전략":"""

# 4. Sidebar parameter controls
target_sidebar = """elif strategy_choice == "스토캐스틱 오실레이터 전략":
    stoch_k = st.sidebar.slider("%K 기간", min_value=5, max_value=30, value=14, step=1)"""

replacement_sidebar = """elif strategy_choice == "200일선 + MACD 추세 필터 전략":
    sma_macd_sma = st.sidebar.slider("장기 이동평균선 (일)", min_value=100, max_value=300, value=200, step=10)
    sma_macd_fast = st.sidebar.slider("MACD 단기 EMA 기간 (일)", min_value=5, max_value=30, value=12, step=1)
    sma_macd_slow = st.sidebar.slider("MACD 장기 EMA 기간 (일)", min_value=20, max_value=60, value=26, step=1)
    sma_macd_signal = st.sidebar.slider("MACD 시그널 EMA 기간 (일)", min_value=3, max_value=20, value=9, step=1)
    sma_macd_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=DUAL_MOMENTUM_ASSET_OPTIONS.index("채권 (안전자산/피신처) | TLT - 장기 미국채 (20년+)") + 1,
        help="현재 종목 입력창의 티커가 공격 자산이고, 조건이 깨지면 여기서 고른 자산 또는 현금으로 이동합니다.",
    )
    if sma_macd_defense_option == "현금":
        sma_macd_defensive_mode = "현금"
        sma_macd_defense_ticker = "CASH"
    elif sma_macd_defense_option == "직접 입력":
        sma_macd_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT")
        sma_macd_defensive_mode = "방어자산"
    else:
        sma_macd_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[sma_macd_defense_option]
        sma_macd_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {sma_macd_defense_ticker}")
    sma_macd_signal_mode_label = st.sidebar.radio(
        "MACD 활용 방식",
        options=["진입 확인용", "상시 필터"],
        horizontal=True,
        help="진입 확인용은 MACD로 진입하고 200일선 이탈 때 청산합니다. 상시 필터는 200일선과 MACD가 모두 양호할 때만 보유합니다.",
    )
    sma_macd_signal_mode = "sma_exit" if sma_macd_signal_mode_label == "진입 확인용" else "strict"
    sma_macd_rebalance_label = st.sidebar.radio("신호 반영 주기", options=["월말", "매일"], horizontal=True)
    sma_macd_rebalance_frequency = "M" if sma_macd_rebalance_label == "월말" else None
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
    dca_monthly_contribution = st.sidebar.slider("매월 추가 적립 금액 (원)", min_value=0, max_value=5000000, value=500000, step=50000)
    dca_frequency = st.sidebar.radio("적립 주기", options=["매월 첫 거래일", "매주 첫 거래일"], horizontal=True)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "스토캐스틱 오실레이터 전략":
    stoch_k = st.sidebar.slider("%K 기간", min_value=5, max_value=30, value=14, step=1)"""

# 5. Strategy Descriptions
target_desc = """    "스토캐스틱 오실레이터 전략": \"\"\""""

replacement_desc = """    "200일선 + MACD 추세 필터 전략": \"\"\"
    **📊 200일선 + MACD 추세 필터 전략**
    - **원리**: 장기 추세는 200일 이동평균선으로 확인하고, 진입 타이밍은 MACD로 보조 확인합니다.
    - **매매 규칙**: 현재 선택한 종목이 장기 이동평균선 위에 있고 MACD가 양호하면 보유합니다. 조건이 깨지면 현금 또는 선택한 방어 자산으로 이동합니다.
    - **특징**: MACD 단독 전략보다 횡보장 신호를 줄이고, 큰 하락장에서 방어를 시도하는 추세 필터 전략입니다.
    \"\"\",
    "적립식 존버 물타기 (DCA) 전략": \"\"\"
    **📅 적립식 존버 물타기 (DCA) 전략**
    - **원리**: 매월/매주 정기적으로 고정된 금액만큼 주식을 기계적으로 추가 매수(물타기)하여 평단가를 낮추는 적립식 투자 전략입니다.
    - **매매 규칙**: 최초 시드머니로 전량 매수한 후, 선택한 주기마다 자동으로 설정한 적립 금액만큼 추가 매수하여 장기 보유합니다.
    - **특징**: 횡보장 및 약세장에서 매입 단가를 낮추어 추후 반등 시 빠른 회복과 안정적인 장기 성과를 추구하는 가장 대중적이고 검증된 존버 전략입니다.
    \"\"\",
    "스토캐스틱 오실레이터 전략": \"\"\""""

# 6. Strategy Length Validation
target_validation = """        elif strategy_choice == "듀얼 모멘텀 전략" and len(df) <= dm_lookback_days:
            st.error(f"데이터의 총 크기({len(df)}일)가 모멘텀 비교 기간({dm_lookback_days}영업일)보다 작습니다. 기간을 늘려주세요.")"""

replacement_validation = """        elif strategy_choice == "듀얼 모멘텀 전략" and len(df) <= dm_lookback_days:
            st.error(f"데이터의 총 크기({len(df)}일)가 모멘텀 비교 기간({dm_lookback_days}영업일)보다 작습니다. 기간을 늘려주세요.")
        elif strategy_choice == "200일선 + MACD 추세 필터 전략" and len(df) <= sma_macd_sma:
            st.error(f"데이터의 총 크기({len(df)}일)가 장기 이동평균 기간({sma_macd_sma}일)보다 작습니다. 기간을 늘려주세요.")"""

# 7. Runner Block
target_runner = """            elif strategy_choice == "스토캐스틱 오실레이터 전략":"""

replacement_runner = """            elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                sma_macd_defense_df = None
                sma_macd_defense_code = "CASH"
                if sma_macd_defensive_mode == "방어자산":
                    sma_macd_defense_code = resolve_ticker_input(sma_macd_defense_ticker)
                    sma_macd_defense_name = get_ticker_name(sma_macd_defense_code)
                    with st.spinner(f"📡 방어 자산 {sma_macd_defense_name} ({sma_macd_defense_code}) 데이터를 불러오는 중..."):
                        sma_macd_defense_df = load_data(start_date, end_date, sma_macd_defense_code)

                    if sma_macd_defense_name == UNKNOWN_TICKER_NAME or sma_macd_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()

                sma_macd_df = run_sma_macd_filter_backtest(
                    attack_df=df,
                    defense_df=sma_macd_defense_df,
                    attack_label=ticker_symbol,
                    defense_label=sma_macd_defense_code.strip().upper(),
                    sma_period=sma_macd_sma,
                    fast_period=sma_macd_fast,
                    slow_period=sma_macd_slow,
                    signal_period=sma_macd_signal,
                    initial_budget=initial_budget,
                    fee_rate_pct=fee_rate,
                    slippage_rate_pct=slippage_rate,
                    rebalance_frequency=sma_macd_rebalance_frequency,
                    defensive_mode=sma_macd_defensive_mode,
                    signal_mode=sma_macd_signal_mode,
                    use_drip=use_drip,
                )
                if sma_macd_df.empty:
                    st.error("❌ 공격 자산과 방어 자산의 공통 거래일 데이터가 부족합니다.")
                    st.stop()

                strategy_final_return = sma_macd_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = sma_macd_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = sma_macd_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = sma_macd_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(sma_macd_df['Position'] != sma_macd_df['Position'].shift(1).fillna("CASH"))
                total_days = len(sma_macd_df)

            elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
                dca_df = run_dca_backtest(
                    df=df,
                    initial_budget=initial_budget,
                    monthly_contribution=dca_monthly_contribution,
                    fee_rate_pct=fee_rate,
                    slippage_rate_pct=slippage_rate,
                    frequency=dca_frequency,
                    use_drip=use_drip
                )
                strategy_final_return = dca_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = dca_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = dca_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = dca_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(dca_df['Buy_Signal'])
                total_days = len(dca_df)

            elif strategy_choice == "스토캐스틱 오실레이터 전략":"""

# 8. Strategy Label Map
target_label = """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                strategy_label_map = {
                    "변동성 돌파 전략 (Larry Williams)": "⚡ 변동성 돌파",
                    "듀얼 모멘텀 전략": "🧭 듀얼 모멘텀",
                    "이동평균선 골든크로스 전략": "📈 이동평균선 크로스",
                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드",
                    "MACD 추세 전략": "📊 MACD 추세",
                }"""

replacement_label = """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "200일선 + MACD 추세 필터 전략", "적립식 존버 물타기 (DCA) 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                strategy_label_map = {
                    "변동성 돌파 전략 (Larry Williams)": "⚡ 변동성 돌파",
                    "듀얼 모멘텀 전략": "🧭 듀얼 모멘텀",
                    "이동평균선 골든크로스 전략": "📈 이동평균선 크로스",
                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드",
                    "MACD 추세 전략": "📊 MACD 추세",
                    "200일선 + MACD 추세 필터 전략": "📊 200일선+MACD",
                    "적립식 존버 물타기 (DCA) 전략": "📅 적립식 DCA",
                }"""

# 9. Charts Plotting
target_charts = """            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                st.subheader(f"{generic_label} 가격 및 신호")"""

replacement_charts = """            elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                st.subheader(f"📊 실제 {ticker_name} 주가 및 200일선 + MACD 추세 필터")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['Attack_Close'], name="공격 자산 종가",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>종가</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['SMA'], name=f"{sma_macd_sma}일 이동평균선",
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>장기 이동평균선</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                position_markers = sma_macd_df[sma_macd_df['Position'] != sma_macd_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['Attack_Close'],
                    mode="markers",
                    name="포지션 전환",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=position_markers['Selected_Asset'],
                    hovertemplate='<b>포지션 전환</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title=""),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="가격"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)

                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['MACD'], name="MACD선",
                    line=dict(color="#9467bd", width=1.5),
                    hovertemplate='<b>MACD선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['Signal'], name="Signal선",
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>Signal선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                colors = np.where(sma_macd_df['Histogram'] >= 0, '#2ca02c', '#d62728')
                fig_macd.add_trace(go.Bar(
                    x=sma_macd_df.index, y=sma_macd_df['Histogram'], name="오실레이터",
                    marker_color=colors,
                    hovertemplate='<b>오실레이터</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=10, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="MACD 수치"),
                    height=220
                )
                st.plotly_chart(fig_macd, use_container_width=True)

            elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
                st.subheader(f"📊 {ticker_name} 적립식 물타기 (DCA) 자산 추이")
                fig_dca = go.Figure()
                fig_dca.add_trace(go.Scatter(
                    x=dca_df.index, y=dca_df['Strategy_Balance'], name="전략 평가 잔고 (원금+수익)",
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>평가 잔고</b><br>날짜: %{x}<br>잔고: %{y:,.0f}원<extra></extra>'
                ))
                fig_dca.add_trace(go.Scatter(
                    x=dca_df.index, y=dca_df['Total_Invested'], name="누적 투자 원금",
                    line=dict(color="#7f7f7f", width=1.5, dash="dash"),
                    hovertemplate='<b>누적 원금</b><br>날짜: %{x}<br>원금: %{y:,.0f}원<extra></extra>'
                ))
                buy_markers = dca_df[dca_df['Buy_Signal']]
                fig_dca.add_trace(go.Scatter(
                    x=buy_markers.index, y=buy_markers['Strategy_Balance'],
                    mode="markers", name="적립식 추가 매수",
                    marker=dict(color="#d62728", size=6, symbol="circle"),
                    hovertemplate='<b>추가 적립 매수</b><br>날짜: %{x}<extra></extra>'
                ))
                fig_dca.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="금액 (원)"),
                    height=300
                )
                st.plotly_chart(fig_dca, use_container_width=True)

            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                st.subheader(f"{generic_label} 가격 및 신호")"""

# 10. Cumulative Return Chart
target_returns = """            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                fig_ret.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['Strategy_Cum_Return'], name=generic_label,"""

replacement_returns = """            elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                fig_ret.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['Strategy_Cum_Return'], name="📊 200일선+MACD 추세 필터",
                    line=dict(color="#e377c2", width=2.5),
                    hovertemplate='<b>200일선+MACD 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=sma_macd_df.index, y=sma_macd_df['Hold_Cum_Return'], name=f"📈 단순 보유 ({ticker_symbol})",
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
                fig_ret.add_trace(go.Scatter(
                    x=dca_df.index, y=dca_df['Strategy_Cum_Return'], name="📅 적립식 DCA 전략 수익률",
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>적립식 DCA</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=dca_df.index, y=dca_df['Hold_Cum_Return'], name=f"📈 단순 보유 ({ticker_symbol})",
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                fig_ret.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['Strategy_Cum_Return'], name=generic_label,"""

# 11. Monthly Stats Mapping
target_stats = """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                if strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                    summary_stats = calculate_vbt_monthly_stats(vbt_df)
                    target_df = vbt_df
                elif strategy_choice == "듀얼 모멘텀 전략":
                    summary_stats = calculate_dual_momentum_monthly_stats(dm_df)
                    target_df = dm_df
                elif strategy_choice == "이동평균선 골든크로스 전략":
                    summary_stats = calculate_ma_cross_monthly_stats(ma_df)
                    target_df = ma_df
                elif strategy_choice == "RSI 과매도 반등 전략":
                    summary_stats = calculate_rsi_monthly_stats(rsi_df)
                    target_df = rsi_df
                elif strategy_choice == "볼린저 밴드 반등 전략":
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df
                elif strategy_choice == "MACD 추세 전략":
                    summary_stats = calculate_macd_monthly_stats(macd_df)
                    target_df = macd_df
                else:
                    is_portfolio = strategy_choice in ["영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]
                    summary_stats = calculate_signal_monthly_stats(generic_df, is_portfolio=is_portfolio)
                    target_df = generic_df"""

replacement_stats = """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "200일선 + MACD 추세 필터 전략", "적립식 존버 물타기 (DCA) 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                if strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                    summary_stats = calculate_vbt_monthly_stats(vbt_df)
                    target_df = vbt_df
                elif strategy_choice == "듀얼 모멘텀 전략":
                    summary_stats = calculate_dual_momentum_monthly_stats(dm_df)
                    target_df = dm_df
                elif strategy_choice == "이동평균선 골든크로스 전략":
                    summary_stats = calculate_ma_cross_monthly_stats(ma_df)
                    target_df = ma_df
                elif strategy_choice == "RSI 과매도 반등 전략":
                    summary_stats = calculate_rsi_monthly_stats(rsi_df)
                    target_df = rsi_df
                elif strategy_choice == "볼린저 밴드 반등 전략":
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df
                elif strategy_choice == "MACD 추세 전략":
                    summary_stats = calculate_macd_monthly_stats(macd_df)
                    target_df = macd_df
                elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                    summary_stats = calculate_sma_macd_monthly_stats(sma_macd_df)
                    target_df = sma_macd_df
                elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
                    summary_stats = calculate_dca_monthly_stats(dca_df)
                    target_df = dca_df
                else:
                    is_portfolio = strategy_choice in ["영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]
                    summary_stats = calculate_signal_monthly_stats(generic_df, is_portfolio=is_portfolio)
                    target_df = generic_df"""

# 12. Columns Formatting
target_columns = """                    if '매수 보유 일수 (일)' in display_stats.columns:
                        display_stats['매수 보유 일수 (일)'] = display_stats['매수 보유 일수 (일)'].map('{:,.0f}일'.format)
                    if '매수 횟수 (회)' in display_stats.columns:
                        display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    if '공격 모멘텀 (%)' in display_stats.columns:
                        display_stats['공격 모멘텀 (%)'] = display_stats['공격 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    if '방어 모멘텀 (%)' in display_stats.columns:
                        display_stats['방어 모멘텀 (%)'] = display_stats['방어 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    display_stats['전략 수익률 (%)'] = display_stats['전략 수익률 (%)'].map('{:+.2f}%'.format)"""

replacement_columns = """                    if '매수 보유 일수 (일)' in display_stats.columns:
                        display_stats['매수 보유 일수 (일)'] = display_stats['매수 보유 일수 (일)'].map('{:,.0f}일'.format)
                    if '매수 횟수 (회)' in display_stats.columns:
                        display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    if '적립 횟수 (회)' in display_stats.columns:
                        display_stats['적립 횟수 (회)'] = display_stats['적립 횟수 (회)'].map('{:,.0f}회'.format)
                    if '월간 추가 적립액 (원)' in display_stats.columns:
                        display_stats['월간 추가 적립액 (원)'] = display_stats['월간 추가 적립액 (원)'].map('{:,.0f}원'.format)
                    if '누적 투자 원금 (원)' in display_stats.columns:
                        display_stats['누적 투자 원금 (원)'] = display_stats['누적 투자 원금 (원)'].map('{:,.0f}원'.format)
                    if '공격 모멘텀 (%)' in display_stats.columns:
                        display_stats['공격 모멘텀 (%)'] = display_stats['공격 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    if '방어 모멘텀 (%)' in display_stats.columns:
                        display_stats['방어 모멘텀 (%)'] = display_stats['방어 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    display_stats['전략 수익률 (%)'] = display_stats['전략 수익률 (%)'].map('{:+.2f}%'.format)"""

# Apply modifications
mods = [
    ("imports", target_imports, replacement_imports),
    ("selectbox", target_selectbox, replacement_selectbox),
    ("defaults", target_defaults, replacement_defaults),
    ("sidebar", target_sidebar, replacement_sidebar),
    ("desc", target_desc, replacement_desc),
    ("validation", target_validation, replacement_validation),
    ("runner", target_runner, replacement_runner),
    ("label", target_label, replacement_label),
    ("charts", target_charts, replacement_charts),
    ("returns", target_returns, replacement_returns),
    ("stats", target_stats, replacement_stats),
    ("columns", target_columns, replacement_columns)
]

modified = True
for name, target, replacement in mods:
    target_lf = target.replace("\r\n", "\n")
    replacement_lf = replacement.replace("\r\n", "\n")
    
    if target_lf in content_lf:
        content_lf = content_lf.replace(target_lf, replacement_lf)
        print(f"Apply '{name}': SUCCESS")
    else:
        print(f"Apply '{name}': FAILED")
        modified = False

if modified:
    dashboard_path.write_text(content_lf, encoding="utf-8")
    print("All strategy changes applied successfully.")
else:
    print("Failed to apply some strategy changes. Aborted save.")
