import subprocess
from pathlib import Path

# Reset dashboard file to clean head state
subprocess.run(["git", "checkout", "chapter3/stock_prediction_dashboard.py"])
content = Path("chapter3/stock_prediction_dashboard.py").read_text(encoding="utf-8")
content = content.replace("\r\n", "\n")

# Trace each target
targets = {
    "imports": """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
)""",
    "selectbox": """        "이동평균선 골든크로스 전략",
        "RSI 과매도 반등 전략",
        "볼린저 밴드 반등 전략",
        "MACD 추세 전략",
        "스토캐스틱 오실레이터 전략\",""",
    "defaults": """dm_lookback_days = 252
dm_defense_ticker = "IEF"
dm_defensive_mode = "방어자산"
if strategy_choice == "머신러닝 롤링 예측 전략":""",
    "sidebar": """elif strategy_choice == "스토캐스틱 오실레이터 전략":
    stoch_k = st.sidebar.slider("%K 기간", min_value=5, max_value=30, value=14, step=1)""",
    "desc": """    "스토캐스틱 오실레이터 전략": \"\"\"""",
    "validation": """        elif strategy_choice == "듀얼 모멘텀 전략" and len(df) <= dm_lookback_days:
            st.error(f"데이터의 총 크기({len(df)}일)가 모멘텀 비교 기간({dm_lookback_days}영업일)보다 작습니다. 기간을 늘려주세요.")""",
    "runner": """            elif strategy_choice == "스토캐스틱 오실레이터 전략":""",
    "label": """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                strategy_label_map = {
                    "변동성 돌파 전략 (Larry Williams)": "⚡ 변동성 돌파",
                    "듀얼 모멘텀 전략": "🧭 듀얼 모멘텀",
                    "이동평균선 골든크로스 전략": "📈 이동평균선 크로스",
                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드",
                    "MACD 추세 전략": "📊 MACD 추세",
                }""",
    "charts": """            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                st.subheader(f"{generic_label} 가격 및 신호")""",
    "returns": """            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                fig_ret.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['Strategy_Cum_Return'], name=generic_label,""",
    "stats": """            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
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
                    target_df = generic_df""",
    "columns": """                    if '매수 보유 일수 (일)' in display_stats.columns:
                        display_stats['매수 보유 일수 (일)'] = display_stats['매수 보유 일수 (일)'].map('{:,.0f}일'.format)
                    if '매수 횟수 (회)' in display_stats.columns:
                        display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    if '공격 모멘텀 (%)' in display_stats.columns:
                        display_stats['공격 모멘텀 (%)'] = display_stats['공격 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    if '방어 모멘텀 (%)' in display_stats.columns:
                        display_stats['방어 모멘텀 (%)'] = display_stats['방어 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    display_stats['전략 수익률 (%)'] = display_stats['전략 수익률 (%)'].map('{:+.2f}%'.format)"""
}

current = content
for name, target in targets.items():
    found = target in current
    print(f"Target '{name}': {'FOUND' if found else 'NOT FOUND'}")
    if found:
        current = current.replace(target, f"### REPLACED_{name.upper()} ###")
