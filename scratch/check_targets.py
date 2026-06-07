from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")
content_lf = content.replace("\r\n", "\n")

target_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
)"""

target_selectbox = '        "200일선 + MACD 추세 필터 전략",'

target_sidebar = 'elif strategy_choice == "스토캐스틱 오실레이터 전략":'

target_desc = '    "스토캐스틱 오실레이터 전략": """'

target_runner = '            elif strategy_choice == "스토캐스틱 오실레이터 전략":'

target_label = '                    "200일선 + MACD 추세 필터 전략": "📊 200일선+MACD",'

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

target_stats = """                elif strategy_choice == "200일선 + MACD 추세 필터 전략":
                    summary_stats = calculate_sma_macd_monthly_stats(sma_macd_df)
                    target_df = sma_macd_df"""

target_columns = """                    if '공격자산 보유 일수 (일)' in display_stats.columns:
                        display_stats['공격자산 보유 일수 (일)'] = display_stats['공격자산 보유 일수 (일)'].map('{:,.0f}일'.format)"""

targets = [
    ("imports", target_imports),
    ("selectbox", target_selectbox),
    ("sidebar", target_sidebar),
    ("desc", target_desc),
    ("runner", target_runner),
    ("label", target_label),
    ("charts", target_charts),
    ("returns", target_returns),
    ("stats", target_stats),
    ("columns", target_columns)
]

for name, t in targets:
    t_lf = t.replace("\r\n", "\n")
    found = t_lf in content_lf
    print(f"Target '{name}': {'FOUND' if found else 'NOT FOUND'}")
