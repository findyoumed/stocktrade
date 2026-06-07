from pathlib import Path
import sys

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")
content_lf = content.replace("\r\n", "\n")

# 1. Update imports
target_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
    run_dca_backtest,
    calculate_dca_monthly_stats,
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
    calculate_sharpe_ratio,
    extract_trades_to_df,
)"""

if target_imports not in content_lf:
    print("Error: Target imports block not found.")
    sys.exit(1)

content_lf = content_lf.replace(target_imports, replacement_imports)

# 2. Add result_df initialization
target_init = "# --- 백테스트 연산 수행 ---"
replacement_init = "# --- 백테스트 연산 수행 ---\n            result_df = None"

if target_init not in content_lf:
    print("Error: Target init block not found.")
    sys.exit(1)

content_lf = content_lf.replace(target_init, replacement_init)

# 3. Add result_df assignment inside each runner block
assignments = [
    ("strategy_final_balance = ml_df['Strategy_Balance'].iloc[-1]", "result_df = ml_df"),
    ("strategy_final_balance = vbt_df['Strategy_Balance'].iloc[-1]", "result_df = vbt_df"),
    ("strategy_final_balance = ma_df['Strategy_Balance'].iloc[-1]", "result_df = ma_df"),
    ("strategy_final_balance = rsi_df['Strategy_Balance'].iloc[-1]", "result_df = rsi_df"),
    ("strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]", "result_df = bb_df"),
    ("strategy_final_balance = dm_df['Strategy_Balance'].iloc[-1]", "result_df = dm_df"),
    ("strategy_final_balance = macd_df['Strategy_Balance'].iloc[-1]", "result_df = macd_df"),
    ("strategy_final_balance = sma_macd_df['Strategy_Balance'].iloc[-1]", "result_df = sma_macd_df"),
    ("strategy_final_balance = dca_df['Strategy_Balance'].iloc[-1]", "result_df = dca_df"),
    ("strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]", "result_df = generic_df"),
]

for target, replacement in assignments:
    if target not in content_lf:
        print(f"Warning: Assignment target '{target}' not found.")
    else:
        # Insert result_df assignment on the next line
        # Find indent of target line
        idx = 0
        while True:
            pos = content_lf.find(target, idx)
            if pos == -1:
                break
            line_start = content_lf.rfind("\n", 0, pos) + 1
            indent = ""
            for char in content_lf[line_start:]:
                if char in [" ", "\t"]:
                    indent += char
                else:
                    break
            new_text = f"{target}\n{indent}{replacement}"
            content_lf = content_lf[:pos] + new_text + content_lf[pos+len(target):]
            idx = pos + len(new_text)
        print(f"Added result_df assignment for target: {target[:50]}...")

# 4. Add second row of metrics (Sharpe Ratio and Win Rate)
target_metrics = """                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")"""

replacement_metrics = """                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")
                
                # Sharpe Ratio & Win Rate 계산 및 출력
                if result_df is not None:
                    strat_sharpe = calculate_sharpe_ratio(result_df['Strategy_Return'])
                    hold_sharpe = calculate_sharpe_ratio(result_df['Hold_Return'])
                    strat_win_rate = (result_df['Strategy_Return'] > 1.0).mean() * 100
                    hold_win_rate = (result_df['Hold_Return'] > 1.0).mean() * 100
                    
                    st.markdown("---")
                    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
                    with col_add1:
                        st.metric(label="📊 전략 샤프 지수 (Sharpe)", value=f"{strat_sharpe:.2f}")
                    with col_add2:
                        st.metric(label="📊 단순 보유 샤프 지수", value=f"{hold_sharpe:.2f}")
                    with col_add3:
                        st.metric(label="🎯 전략 일간 승률", value=f"{strat_win_rate:.2f}%")
                    with col_add4:
                        st.metric(label="🎯 단순 보유 일간 승률", value=f"{hold_win_rate:.2f}%")"""

if target_metrics not in content_lf:
    print("Error: Target metrics block not found.")
    sys.exit(1)

content_lf = content_lf.replace(target_metrics, replacement_metrics)

# 5. Add transaction logs expander before st.divider()
target_divider = "            st.divider()\n            render_financial_data_section(ticker_code, ticker_name)"

replacement_divider = """            # --- 구조 5: 상세 거래 내역 / 적립 내역 조회 ---
            if strategy_choice != "두 전략 통합 비교":
                if result_df is not None:
                    st.subheader("🔎 상세 거래 / 적립 내역 조회")
                    trades_df = extract_trades_to_df(
                        result_df,
                        strategy_choice,
                        initial_budget,
                        fee_rate,
                        slippage_rate
                    )
                    if not trades_df.empty:
                        with st.expander("👉 여기를 클릭하여 상세 매수/매도 내역 테이블 펼치기", expanded=False):
                            st.dataframe(trades_df.sort_index(ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ 해당 기간 동안 체결된 거래 내역이 없습니다.")
            else:
                # 두 전략 통합 비교 모드
                st.subheader("🔎 전략별 상세 거래 내역 조회")
                col_ml_trades, col_vbt_trades = st.columns(2)
                with col_ml_trades:
                    st.write("🤖 **머신러닝 예측 전략 상세 거래 내역**")
                    ml_trades = extract_trades_to_df(ml_df, "머신러닝 롤링 예측 전략", initial_budget, fee_rate, slippage_rate)
                    if not ml_trades.empty:
                        with st.expander("🤖 머신러닝 거래 내역 펼치기", expanded=False):
                            st.dataframe(ml_trades.sort_index(ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.caption("체결된 거래 내역 없음")
                with col_vbt_trades:
                    st.write("⚡ **변동성 돌파 전략 상세 거래 내역**")
                    vbt_trades = extract_trades_to_df(vbt_df, "변동성 돌파 전략 (Larry Williams)", initial_budget, fee_rate, slippage_rate)
                    if not vbt_trades.empty:
                        with st.expander("⚡ 변동성 돌파 거래 내역 펼치기", expanded=False):
                            st.dataframe(vbt_trades.sort_index(ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.caption("체결된 거래 내역 없음")

            st.divider()
            render_financial_data_section(ticker_code, ticker_name)"""

if target_divider not in content_lf:
    print("Error: Target divider block not found.")
    sys.exit(1)

content_lf = content_lf.replace(target_divider, replacement_divider)

dashboard_path.write_text(content_lf, encoding="utf-8")
print("Successfully updated stock_prediction_dashboard.py")
