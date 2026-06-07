import sys
import re
from pathlib import Path

# --- Part 1: Modify backtest_engine.py ---
engine_path = Path("chapter3/backtest_engine.py")
engine_code = engine_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1.1 exit_cost in non-VBT strategies
exit_cost_old = "exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)"
exit_cost_new = "exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)"
engine_code = engine_code.replace(exit_cost_old, exit_cost_new)

exit_cost_ma_old = "exit_cost = np.where((ma_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)"
exit_cost_ma_new = "exit_cost = np.where((ma_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)"
engine_code = engine_code.replace(exit_cost_ma_old, exit_cost_ma_new)

exit_cost_rsi_old = "exit_cost = np.where((rsi_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)"
exit_cost_rsi_new = "exit_cost = np.where((rsi_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)"
engine_code = engine_code.replace(exit_cost_rsi_old, exit_cost_rsi_new)

exit_cost_bb_old = "exit_cost = np.where((bb_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)"
exit_cost_bb_new = "exit_cost = np.where((bb_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)"
engine_code = engine_code.replace(exit_cost_bb_old, exit_cost_bb_new)

exit_cost_macd_old = "exit_cost = np.where((macd_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)"
exit_cost_macd_new = "exit_cost = np.where((macd_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)"
engine_code = engine_code.replace(exit_cost_macd_old, exit_cost_macd_new)

# 1.2 exit cost in run_vbt_backtest
vbt_cost_old = "(vbt_df['종가'] * (1 - cost_rate)) / (vbt_df['Buy_Price'] * (1 + cost_rate)) + strategy_div_yield"
vbt_cost_new = "(vbt_df['종가'] * (1 - cost_rate - 0.18 / 100)) / (vbt_df['Buy_Price'] * (1 + cost_rate)) + strategy_div_yield"
engine_code = engine_code.replace(vbt_cost_old, vbt_cost_new)

# 1.3 Trade_Cost in run_dual_momentum_backtest and run_sma_macd_filter_backtest
trade_cost_old = """    combined['Trade_Cost'] = np.select(
        [
            ~changed,
            (prev_position == "CASH") | (combined['Position'] == "CASH"),
        ],
        [
            0.0,
            cost_rate,
        ],
        default=2 * cost_rate
    )"""

trade_cost_new = """    conds = [
        ~changed,
        (prev_position == "ATTACK") & (combined['Position'] == "CASH"),
        (prev_position == "ATTACK") & (combined['Position'] == "DEFENSE"),
        (prev_position == "CASH") | (combined['Position'] == "CASH"),
    ]
    outputs = [
        0.0,
        cost_rate + 0.18 / 100,
        2 * cost_rate + 0.18 / 100,
        cost_rate,
    ]
    combined['Trade_Cost'] = np.select(conds, outputs, default=2 * cost_rate)"""

engine_code = engine_code.replace(trade_cost_old, trade_cost_new)

trade_cost_old_2 = """    combined['Trade_Cost'] = np.select(
        [
            ~changed,
            (prev_position == "CASH") | (combined['Position'] == "CASH"),
        ],
        [
            0.0,
            cost_rate,
        ],
        default=2 * cost_rate,
    )"""

trade_cost_new_2 = """    conds = [
        ~changed,
        (prev_position == "ATTACK") & (combined['Position'] == "CASH"),
        (prev_position == "ATTACK") & (combined['Position'] == "DEFENSE"),
        (prev_position == "CASH") | (combined['Position'] == "CASH"),
    ]
    outputs = [
        0.0,
        cost_rate + 0.18 / 100,
        2 * cost_rate + 0.18 / 100,
        cost_rate,
    ]
    combined['Trade_Cost'] = np.select(conds, outputs, default=2 * cost_rate)"""

engine_code = engine_code.replace(trade_cost_old_2, trade_cost_new_2)

# 1.4 Append calculate_max_consecutive_losses
consec_loss_func = """

def calculate_max_consecutive_losses(returns_series):
    \"\"\"일간 수익률 시리즈를 기반으로 최대 연속 손실 일수를 계산합니다.
    returns_series는 각 일자별 전략 수익률 비율(예: 1.01이면 +1% 수익)을 나타냅니다.
    \"\"\"
    if returns_series is None or len(returns_series) == 0:
        return 0
    is_loss = returns_series < 1.0
    consecutive = is_loss.groupby((~is_loss).cumsum()).cumsum()
    return int(consecutive.max())
"""
if "calculate_max_consecutive_losses" not in engine_code:
    engine_code += consec_loss_func

engine_path.write_text(engine_code, encoding="utf-8")
print("Successfully modified backtest_engine.py")


# --- Part 2: Modify stock_prediction_dashboard.py ---
dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
dashboard_code = dashboard_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 2.1 Update imports
imports_old = """from backtest_engine import (
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

imports_new = """from backtest_engine import (
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
    calculate_max_consecutive_losses,
)"""
dashboard_code = dashboard_code.replace(imports_old, imports_new)

# 2.2 Add validate_ticker_input helper function
target_helper_insert = "UNKNOWN_TICKER_NAME = \"알 수 없는 종목\""
helper_func = """import re

def validate_ticker_input(text, field_name="종목명"):
    if not text:
        return True
    if len(text) > 30:
        st.sidebar.error(f"⚠️ {field_name}이 너무 깁니다. (최대 30자)")
        return False
    # 한글, 영문, 숫자, 공백, 괄호(), &, /, ., - 만 허용 (한영 혼합 가능)
    if not re.match(r"^[가-힣a-zA-Z0-9\\s()&./\\-]*$", text):
        st.sidebar.error(f"⚠️ {field_name}에 허용되지 않은 특수문자가 포함되어 있습니다. (한글, 영문, 숫자, 공백, 괄호, &, /, ., - 만 허용)")
        return False
    return True

UNKNOWN_TICKER_NAME = "알 수 없는 종목\""""

if "def validate_ticker_input" not in dashboard_code:
    dashboard_code = dashboard_code.replace(target_helper_insert, helper_func)

# 2.3 Add validation calls with correct indentations
target_validate_1 = 'ticker_input = st.sidebar.text_input("🔍 종목 코드/종목명 직접 입력 (예: SPY, 삼성전자, 005930)", key="target_ticker")'
replacement_validate_1 = 'ticker_input = st.sidebar.text_input("🔍 종목 코드/종목명 직접 입력 (예: SPY, 삼성전자, 005930)", key="target_ticker")\nif not validate_ticker_input(ticker_input, "종목 입력"): st.stop()'
dashboard_code = dashboard_code.replace(target_validate_1, replacement_validate_1)

target_validate_2 = 'dm_defense_ticker = st.sidebar.text_input("비교/방어 자산 티커 직접 입력", "IEF")'
replacement_validate_2 = 'dm_defense_ticker = st.sidebar.text_input("비교/방어 자산 티커 직접 입력", "IEF")\n        if not validate_ticker_input(dm_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()'
dashboard_code = dashboard_code.replace(target_validate_2, replacement_validate_2)

target_validate_3 = 'sma_macd_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT")'
replacement_validate_3 = 'sma_macd_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT")\n        if not validate_ticker_input(sma_macd_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()'
dashboard_code = dashboard_code.replace(target_validate_3, replacement_validate_3)

# 2.4 Update finalize_signal_backtest sell tax
target_finalize_sell = """        elif prev_position and not position:
            # 주식 -> 현금 (매도 청산): 당일은 현금 보유 상태이므로 주가 변동을 반영하지 않고 수수료만 차감
            ret = 1.0 - cost_rate"""

replacement_finalize_sell = """        elif prev_position and not position:
            # 주식 -> 현금 (매도 청산): 수수료 + 매도 거래세(0.18%) 차감
            ret = 1.0 - (cost_rate + 0.18 / 100)"""
dashboard_code = dashboard_code.replace(target_finalize_sell, replacement_finalize_sell)

# 2.5 Update metrics display to include Max Consecutive Losses
target_metrics_display = """                # Sharpe Ratio & Win Rate 계산 및 출력
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

replacement_metrics_display = """                # Sharpe Ratio & Win Rate & Max Consecutive Losses 계산 및 출력
                if result_df is not None:
                    strat_sharpe = calculate_sharpe_ratio(result_df['Strategy_Return'])
                    hold_sharpe = calculate_sharpe_ratio(result_df['Hold_Return'])
                    strat_win_rate = (result_df['Strategy_Return'] > 1.0).mean() * 100
                    hold_win_rate = (result_df['Hold_Return'] > 1.0).mean() * 100
                    strat_consec_losses = calculate_max_consecutive_losses(result_df['Strategy_Return'])
                    hold_consec_losses = calculate_max_consecutive_losses(result_df['Hold_Return'])
                    
                    st.markdown("---")
                    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
                    with col_add1:
                        st.metric(label="📊 전략 샤프 지수 (Sharpe)", value=f"{strat_sharpe:.2f}")
                    with col_add2:
                        st.metric(label="📊 단순 보유 샤프 지수", value=f"{hold_sharpe:.2f}")
                    with col_add3:
                        st.metric(label="🎯 전략 일간 승률", value=f"{strat_win_rate:.2f}%")
                    with col_add4:
                        st.metric(label="🎯 단순 보유 일간 승률", value=f"{hold_win_rate:.2f}%")
                        
                    col_add5, col_add6, col_add7, col_add8 = st.columns(4)
                    with col_add5:
                        st.metric(label="📉 전략 최대 연속 손실", value=f"{strat_consec_losses} 일")
                    with col_add6:
                        st.metric(label="📉 단순 보유 최대 연속 손실", value=f"{hold_consec_losses} 일")"""
dashboard_code = dashboard_code.replace(target_metrics_display, replacement_metrics_display)

dashboard_path.write_text(dashboard_code, encoding="utf-8")
print("Successfully modified stock_prediction_dashboard.py")
