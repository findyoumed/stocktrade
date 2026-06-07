from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# 1. Update Imports
target_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
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

# 2. Update strategy_choice selectbox list
target_selectbox = '        "200일선 + MACD 추세 필터 전략",'
replacement_selectbox = '        "200일선 + MACD 추세 필터 전략",\n        "적립식 존버 물타기 (DCA) 전략",'

# 3. Add DCA sidebar parameters (uniquely matched using newline prefix)
target_sidebar = '\nelif strategy_choice == "스토캐스틱 오실레이터 전략":'
replacement_sidebar = """
elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
    dca_monthly_contribution = st.sidebar.slider("매월 추가 적립 금액 (원)", min_value=0, max_value=5000000, value=500000, step=50000)
    dca_frequency = st.sidebar.radio("적립 주기", options=["매월 첫 거래일", "매주 첫 거래일"], horizontal=True)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "스토캐스틱 오실레이터 전략":"""

# 4. Add DCA strategy description
target_desc = '    "스토캐스틱 오실레이터 전략": """'
replacement_desc = """    "적립식 존버 물타기 (DCA) 전략": \"\"\"
    **📅 적립식 존버 물타기 (DCA) 전략**
    - **원리**: 매월/매주 정기적으로 고정된 금액만큼 주식을 기계적으로 추가 매수(물타기)하여 평단가를 낮추는 적립식 투자 전략입니다.
    - **매매 규칙**: 최초 시드머니로 전량 매수한 후, 선택한 주기마다 자동으로 설정한 적립 금액만큼 추가 매수하여 장기 보유합니다.
    - **특징**: 횡보장 및 약세장에서 매입 단가를 낮추어 추후 반등 시 빠른 회복과 안정적인 장기 성과를 추구하는 가장 대중적이고 검증된 존버 전략입니다.
    \"\"\",
    "스토캐스틱 오실레이터 전략": \"\"\""""

# 5. Add DCA strategy runner
target_runner = '            elif strategy_choice == "스토캐스틱 오실레이터 전략":'
replacement_runner = """            elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
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

# 6. Add DCA strategy label mapping
target_label = '                    "200일선 + MACD 추세 필터 전략": "📊 200일선+MACD",'
replacement_label = '                    "200일선 + MACD 추세 필터 전략": "📊 200일선+MACD",\n                    "적립식 존버 물타기 (DCA) 전략": "📅 적립식 DCA",'

# 7. Add DCA charts rendering (Targeting the transition from 200일선+MACD charts block)
target_charts = """                fig_macd.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=10, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="MACD 수치"),
                    height=220
                )
                st.plotly_chart(fig_macd, use_container_width=True)

            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:"""

replacement_charts = """                fig_macd.update_layout(
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

            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:"""

# 8. Add DCA cumulative returns line chart trace
target_returns = """            elif strategy_choice == "200일선 + MACD 추세 필터 전략":
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
            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:"""

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
            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:"""

# 9. Add DCA monthly stats mapping
target_stats = """                elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                    summary_stats = calculate_sma_macd_monthly_stats(sma_macd_df)
                    target_df = sma_macd_df"""

replacement_stats = """                elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                    summary_stats = calculate_sma_macd_monthly_stats(sma_macd_df)
                    target_df = sma_macd_df
                elif strategy_choice == "적립식 존버 물타기 (DCA) 전략":
                    summary_stats = calculate_dca_monthly_stats(dca_df)
                    target_df = dca_df"""

# 10. Add DCA monthly stats column mappings
target_columns = """                    if '공격자산 보유 일수 (일)' in display_stats.columns:
                        display_stats['공격자산 보유 일수 (일)'] = display_stats['공격자산 보유 일수 (일)'].map('{:,.0f}일'.format)"""

replacement_columns = """                    if '공격자산 보유 일수 (일)' in display_stats.columns:
                        display_stats['공격자산 보유 일수 (일)'] = display_stats['공격자산 보유 일수 (일)'].map('{:,.0f}일'.format)
                    if '적립 횟수 (회)' in display_stats.columns:
                        display_stats['적립 횟수 (회)'] = display_stats['적립 횟수 (회)'].map('{:,.0f}회'.format)
                    if '월간 추가 적립액 (원)' in display_stats.columns:
                        display_stats['월간 추가 적립액 (원)'] = display_stats['월간 추가 적립액 (원)'].map('{:,.0f}원'.format)
                    if '누적 투자 원금 (원)' in display_stats.columns:
                        display_stats['누적 투자 원금 (원)'] = display_stats['누적 투자 원금 (원)'].map('{:,.0f}원'.format)"""

# Apply modifications with debug printing
mods = [
    ("imports", target_imports, replacement_imports),
    ("selectbox", target_selectbox, replacement_selectbox),
    ("sidebar", target_sidebar, replacement_sidebar),
    ("desc", target_desc, replacement_desc),
    ("runner", target_runner, replacement_runner),
    ("label", target_label, replacement_label),
    ("charts", target_charts, replacement_charts),
    ("returns", target_returns, replacement_returns),
    ("stats", target_stats, replacement_stats),
    ("columns", target_columns, replacement_columns)
]

for name, target, replacement in mods:
    content_lf = content.replace("\r\n", "\n")
    target_lf = target.replace("\r\n", "\n")
    replacement_lf = replacement.replace("\r\n", "\n")
    
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf)
        print(f"Step '{name}': SUCCESS")
    else:
        print(f"Step '{name}': FAILED")

dashboard_path.write_text(content, encoding="utf-8")
print("Saved debugged changes.")
