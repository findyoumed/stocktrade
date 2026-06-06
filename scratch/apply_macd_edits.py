import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# 1. Add charts import if missing
if "from charts import add_dividend_markers_to_fig" not in content:
    content = content.replace("from datetime import datetime", "from datetime import datetime\nfrom charts import add_dividend_markers_to_fig")

# 2. Add MACD to options list
# We can find "볼린저 밴드 반등 전략" and append "MACD 추세 전략"
target_options = '"볼린저 밴드 반등 전략"\n    ]'
replacement_options = '"볼린저 밴드 반등 전략",\n        "MACD 추세 전략"\n    ]'
content = content.replace(target_options, replacement_options)

# 3. Add MACD parameters in sidebar
# Find the Bollinger parameters block and append MACD parameters after it
target_params = """elif strategy_choice == "볼린저 밴드 반등 전략":
    bb_period = st.sidebar.slider("이동평균 기간 (일)", min_value=5, max_value=50, value=20, step=5)
    bb_std = st.sidebar.slider("표준편차 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    ma_short, ma_long = 20, 60"""

replacement_params = """elif strategy_choice == "볼린저 밴드 반등 전략":
    bb_period = st.sidebar.slider("이동평균 기간 (일)", min_value=5, max_value=50, value=20, step=5)
    bb_std = st.sidebar.slider("표준편차 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    ma_short, ma_long = 20, 60
elif strategy_choice == "MACD 추세 전략":
    macd_fast = st.sidebar.slider("단기 EMA 기간 (일)", min_value=5, max_value=30, value=12, step=1)
    macd_slow = st.sidebar.slider("장기 EMA 기간 (일)", min_value=20, max_value=60, value=26, step=1)
    macd_signal = st.sidebar.slider("시그널 EMA 기간 (일)", min_value=3, max_value=20, value=9, step=1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60"""

content = content.replace(target_params, replacement_params)

# 4. Add MACD execution logic
# Find Bollinger Band execution block and append MACD execution block
target_exec = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                bb_df = run_bollinger_backtest(df, bb_period, bb_std, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = bb_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = bb_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = bb_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(bb_df['Buy_Signal'] & (~bb_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(bb_df)"""

replacement_exec = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                bb_df = run_bollinger_backtest(df, bb_period, bb_std, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = bb_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = bb_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = bb_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(bb_df['Buy_Signal'] & (~bb_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(bb_df)
            elif strategy_choice == "MACD 추세 전략":
                macd_df = run_macd_backtest(df, macd_fast, macd_slow, macd_signal, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = macd_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = macd_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = macd_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = macd_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(macd_df['Buy_Signal'] & (~macd_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(macd_df)"""

content = content.replace(target_exec, replacement_exec)

# 5. Add MACD to metrics rendering
# Find strategy_label_name mapping and append MACD entry
target_metrics_in = 'elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략"]:'
replacement_metrics_in = 'elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략"]:'
content = content.replace(target_metrics_in, replacement_metrics_in)

target_metrics_map = """                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드"
                }[strategy_choice]"""

replacement_metrics_map = """                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드",
                    "MACD 추세 전략": "📊 MACD 추세"
                }[strategy_choice]"""

content = content.replace(target_metrics_map, replacement_metrics_map)

# 6. Add MACD charts
# Find Bollinger Band chart block and append MACD charts after it
target_chart = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                st.subheader(f"🔘 실제 {ticker_name} 주가 및 볼린저 밴드")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Mid'], name="중간선 (SMA)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>중간선</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Upper_Band'], name="상단 밴드", 
                    line=dict(color="#2ca02c", width=1),
                    hovertemplate='<b>상단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Lower_Band'], name="하단 밴드", 
                    line=dict(color="#d62728", width=1),
                    hovertemplate='<b>하단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)"""

replacement_chart = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                st.subheader(f"🔘 실제 {ticker_name} 주가 및 볼린저 밴드")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Mid'], name="중간선 (SMA)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>중간선</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Upper_Band'], name="상단 밴드", 
                    line=dict(color="#2ca02c", width=1),
                    hovertemplate='<b>상단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Lower_Band'], name="하단 밴드", 
                    line=dict(color="#d62728", width=1),
                    hovertemplate='<b>하단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
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
            elif strategy_choice == "MACD 추세 전략":
                st.subheader(f"📊 실제 {ticker_name} 주가 및 MACD 신호 지표")
                
                # 1. 주가 차트
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title=""),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
                # 2. MACD 지표 차트
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['MACD'], name="MACD선",
                    line=dict(color="#9467bd", width=1.5),
                    hovertemplate='<b>MACD선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Signal'], name="Signal선",
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>Signal선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                colors = np.where(macd_df['Histogram'] >= 0, '#2ca02c', '#d62728')
                fig_macd.add_trace(go.Bar(
                    x=macd_df.index, y=macd_df['Histogram'], name="오실레이터",
                    marker_color=colors,
                    hovertemplate='<b>오실레이터</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=10, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="MACD 수치"),
                    height=200
                )
                st.plotly_chart(fig_macd, use_container_width=True)"""

content = content.replace(target_chart, replacement_chart)

# 7. Add MACD cumulative return chart
target_cum_bb = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Strategy_Cum_Return'], name="🔘 볼린저 밴드 전략", 
                    line=dict(color="#17becf", width=2.5),
                    hovertemplate='<b>볼린저 밴드 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))"""

replacement_cum_bb = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Strategy_Cum_Return'], name="🔘 볼린저 밴드 전략", 
                    line=dict(color="#17becf", width=2.5),
                    hovertemplate='<b>볼린저 밴드 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "MACD 추세 전략":
                fig_ret.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Strategy_Cum_Return'], name="📊 MACD 추세 전략", 
                    line=dict(color="#e377c2", width=2.5),
                    hovertemplate='<b>MACD 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))"""

content = content.replace(target_cum_bb, replacement_cum_bb)

# 8. Add MACD monthly stats logic
target_monthly_in = 'elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략"]:'
replacement_monthly_in = 'elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략"]:'
content = content.replace(target_monthly_in, replacement_monthly_in)

target_monthly = """                else:
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df"""

replacement_monthly = """                elif strategy_choice == "볼린저 밴드 반등 전략":
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df
                else:
                    summary_stats = calculate_macd_monthly_stats(macd_df)
                    target_df = macd_df"""

content = content.replace(target_monthly, replacement_monthly)

dashboard_path.write_text(content, encoding="utf-8")
print("Successfully applied MACD updates with robust replacements!")
