import re

filepath = r"d:\work\stocktrade\chapter3\stock_prediction_dashboard.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports
old_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
    run_dca_backtest,
    calculate_dca_monthly_stats,
    run_custom_static_allocation_backtest,
    calculate_custom_static_allocation_monthly_stats,
)"""

new_imports = """from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    calculate_sma_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
    run_sma_macd_filter_backtest,
    run_dca_backtest,
    calculate_dca_monthly_stats,
    run_custom_static_allocation_backtest,
    calculate_custom_static_allocation_monthly_stats,
    run_ml_backtest,
    calculate_ml_monthly_stats,
    run_vbt_backtest,
    calculate_vbt_monthly_stats,
    run_ma_cross_backtest,
    calculate_ma_cross_monthly_stats,
    run_rsi_backtest,
    calculate_rsi_monthly_stats,
    run_bollinger_backtest,
    calculate_bb_monthly_stats,
)"""

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print("Updated imports.")
else:
    print("Warning: old imports not found exactly.")

# 2. Remove duplicate functions
funcs = [
    "run_ml_backtest",
    "calculate_ml_monthly_stats",
    "run_vbt_backtest",
    "calculate_vbt_monthly_stats",
    "run_ma_cross_backtest",
    "calculate_ma_cross_monthly_stats",
    "run_rsi_backtest",
    "calculate_rsi_monthly_stats",
    "run_bollinger_backtest",
    "calculate_bb_monthly_stats",
]

for func in funcs:
    pattern = r"def " + func + r"\(.*?\):(?:\n|.)*?(?=\n\n(?:def|#|class|if\b|\Z))"
    if re.search(pattern, content):
        content = re.sub(pattern, "", content)
        print(f"Removed duplicate function: {func}")
    else:
        print(f"Warning: could not find duplicate function {func}")

# 3. Add default defense variable values globally in sidebar setup
old_params = """# 5. 전략별 개별 설정
st.sidebar.subheader("🎯 전략 파라미터")
dm_lookback_days = 252"""

new_params = """# 5. 전략별 개별 설정
st.sidebar.subheader("🎯 전략 파라미터")
# [LOG: 20260608_1010] 모든 개별 단일 자산 전략의 방어 자산 변수 기본값 정의
ml_defense_ticker = "CASH"
ml_defensive_mode = "현금"
vbt_defense_ticker = "CASH"
vbt_defensive_mode = "현금"
ma_defense_ticker = "CASH"
ma_defensive_mode = "현금"
rsi_defense_ticker = "CASH"
rsi_defensive_mode = "현금"
bb_defense_ticker = "CASH"
bb_defensive_mode = "현금"
macd_defense_ticker = "CASH"
macd_defensive_mode = "현금"
dm_lookback_days = 252"""

if old_params in content:
    content = content.replace(old_params, new_params)
    print("Inserted global defense variables.")
else:
    print("Warning: old_params not found.")

# 4. Insert sidebar UI options for each strategy
# ML
old_ml_ui = """if strategy_choice == "머신러닝 롤링 예측 전략":
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = 0.5"""

new_ml_ui = """if strategy_choice == "머신러닝 롤링 예측 전략":
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    # [LOG: 20260608_1015] 머신러닝 전략 방어 자산 설정 UI
    ml_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="ml_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if ml_defense_option == "현금":
        ml_defensive_mode = "현금"
        ml_defense_ticker = "CASH"
    elif ml_defense_option == "직접 입력":
        ml_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="ml_def_tick_input")
        if not validate_ticker_input(ml_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        ml_defensive_mode = "방어자산"
    else:
        ml_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[ml_defense_option]
        ml_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {ml_defense_ticker}")
    K = 0.5"""

if old_ml_ui in content:
    content = content.replace(old_ml_ui, new_ml_ui)
    print("Added ML sidebar UI.")

# VBT
old_vbt_ui = """elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    window_size = 90"""

new_vbt_ui = """elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    # [LOG: 20260608_1016] 변동성 돌파 전략 방어 자산 설정 UI
    vbt_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="vbt_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if vbt_defense_option == "현금":
        vbt_defensive_mode = "현금"
        vbt_defense_ticker = "CASH"
    elif vbt_defense_option == "직접 입력":
        vbt_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="vbt_def_tick_input")
        if not validate_ticker_input(vbt_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        vbt_defensive_mode = "방어자산"
    else:
        vbt_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[vbt_defense_option]
        vbt_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {vbt_defense_ticker}")
    window_size = 90"""

if old_vbt_ui in content:
    content = content.replace(old_vbt_ui, new_vbt_ui)
    print("Added VBT sidebar UI.")

# MA Cross
old_ma_ui = """elif strategy_choice == "이동평균선 골든크로스 전략":
    ma_short = st.sidebar.slider("단기 이동평균선 (일)", min_value=5, max_value=50, value=20, step=5)
    ma_long = st.sidebar.slider("장기 이동평균선 (일)", min_value=20, max_value=200, value=60, step=10)
    window_size = 90"""

new_ma_ui = """elif strategy_choice == "이동평균선 골든크로스 전략":
    ma_short = st.sidebar.slider("단기 이동평균선 (일)", min_value=5, max_value=50, value=20, step=5)
    ma_long = st.sidebar.slider("장기 이동평균선 (일)", min_value=20, max_value=200, value=60, step=10)
    # [LOG: 20260608_1017] 이동평균선 크로스 전략 방어 자산 설정 UI
    ma_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="ma_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if ma_defense_option == "현금":
        ma_defensive_mode = "현금"
        ma_defense_ticker = "CASH"
    elif ma_defense_option == "직접 입력":
        ma_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="ma_def_tick_input")
        if not validate_ticker_input(ma_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        ma_defensive_mode = "방어자산"
    else:
        ma_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[ma_defense_option]
        ma_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {ma_defense_ticker}")
    window_size = 90"""

if old_ma_ui in content:
    content = content.replace(old_ma_ui, new_ma_ui)
    print("Added MA sidebar UI.")

# RSI
old_rsi_ui = """elif strategy_choice == "RSI 과매도 반등 전략":
    rsi_period = st.sidebar.slider("RSI 계산 기간 (일)", min_value=5, max_value=30, value=14, step=1)
    buy_rsi = st.sidebar.slider("매수 기준 RSI (이하)", min_value=10, max_value=50, value=30, step=5)
    sell_rsi = st.sidebar.slider("매도 기준 RSI (이상)", min_value=50, max_value=90, value=70, step=5)
    window_size = 90"""

new_rsi_ui = """elif strategy_choice == "RSI 과매도 반등 전략":
    rsi_period = st.sidebar.slider("RSI 계산 기간 (일)", min_value=5, max_value=30, value=14, step=1)
    buy_rsi = st.sidebar.slider("매수 기준 RSI (이하)", min_value=10, max_value=50, value=30, step=5)
    sell_rsi = st.sidebar.slider("매도 기준 RSI (이상)", min_value=50, max_value=90, value=70, step=5)
    # [LOG: 20260608_1018] RSI 전략 방어 자산 설정 UI
    rsi_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="rsi_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if rsi_defense_option == "현금":
        rsi_defensive_mode = "현금"
        rsi_defense_ticker = "CASH"
    elif rsi_defense_option == "직접 입력":
        rsi_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="rsi_def_tick_input")
        if not validate_ticker_input(rsi_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        rsi_defensive_mode = "방어자산"
    else:
        rsi_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[rsi_defense_option]
        rsi_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {rsi_defense_ticker}")
    window_size = 90"""

if old_rsi_ui in content:
    content = content.replace(old_rsi_ui, new_rsi_ui)
    print("Added RSI sidebar UI.")

# BB
old_bb_ui = """elif strategy_choice == "볼린저 밴드 반등 전략":
    bb_period = st.sidebar.slider("이동평균 기간 (일)", min_value=5, max_value=50, value=20, step=5)
    bb_std = st.sidebar.slider("표준편차 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    window_size = 90"""

new_bb_ui = """elif strategy_choice == "볼린저 밴드 반등 전략":
    bb_period = st.sidebar.slider("이동평균 기간 (일)", min_value=5, max_value=50, value=20, step=5)
    bb_std = st.sidebar.slider("표준편차 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    # [LOG: 20260608_1019] 볼린저 밴드 전략 방어 자산 설정 UI
    bb_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="bb_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if bb_defense_option == "현금":
        bb_defensive_mode = "현금"
        bb_defense_ticker = "CASH"
    elif bb_defense_option == "직접 입력":
        bb_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="bb_def_tick_input")
        if not validate_ticker_input(bb_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        bb_defensive_mode = "방어자산"
    else:
        bb_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[bb_defense_option]
        bb_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {bb_defense_ticker}")
    window_size = 90"""

if old_bb_ui in content:
    content = content.replace(old_bb_ui, new_bb_ui)
    print("Added Bollinger sidebar UI.")

# MACD
old_macd_ui = """elif strategy_choice == "MACD 추세 전략":
    macd_fast = st.sidebar.slider("단기 EMA 기간 (일)", min_value=5, max_value=30, value=12, step=1)
    macd_slow = st.sidebar.slider("장기 EMA 기간 (일)", min_value=20, max_value=60, value=26, step=1)
    macd_signal = st.sidebar.slider("시그널 EMA 기간 (일)", min_value=3, max_value=20, value=9, step=1)
    window_size = 90"""

new_macd_ui = """elif strategy_choice == "MACD 추세 전략":
    macd_fast = st.sidebar.slider("단기 EMA 기간 (일)", min_value=5, max_value=30, value=12, step=1)
    macd_slow = st.sidebar.slider("장기 EMA 기간 (일)", min_value=20, max_value=60, value=26, step=1)
    macd_signal = st.sidebar.slider("시그널 EMA 기간 (일)", min_value=3, max_value=20, value=9, step=1)
    # [LOG: 20260608_1020] MACD 전략 방어 자산 설정 UI
    macd_defense_option = st.sidebar.selectbox(
        "조건 불충족 시 이동할 자산",
        options=["현금", *DUAL_MOMENTUM_ASSET_OPTIONS],
        index=0,
        key="macd_defense_opt",
        help="조건이 깨질 때 이동할 자산 또는 현금을 선택합니다."
    )
    if macd_defense_option == "현금":
        macd_defensive_mode = "현금"
        macd_defense_ticker = "CASH"
    elif macd_defense_option == "직접 입력":
        macd_defense_ticker = st.sidebar.text_input("방어 자산 티커 직접 입력", "TLT", key="macd_def_tick_input")
        if not validate_ticker_input(macd_defense_ticker, "방어 자산 티커 직접 입력"): st.stop()
        macd_defensive_mode = "방어자산"
    else:
        macd_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[macd_defense_option]
        macd_defensive_mode = "방어자산"
        st.sidebar.caption(f"선택된 방어 자산: {macd_defense_ticker}")
    window_size = 90"""

if old_macd_ui in content:
    content = content.replace(old_macd_ui, new_macd_ui)
    print("Added MACD sidebar UI.")


# 5. Replace backtest execution blocks with defense logic
# ML
old_ml_exec = """            if strategy_choice == "머신러닝 롤링 예측 전략":
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                ml_df = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(ml_df['Buy_Signal'] & (~ml_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(ml_df)"""

new_ml_exec = """            if strategy_choice == "머신러닝 롤링 예측 전략":
                # [LOG: 20260608_1025] 머신러닝 전략 방어자산 데이터 로드 및 적용
                ml_defense_df = None
                ml_defense_code = "CASH"
                if ml_defensive_mode == "방어자산":
                    ml_defense_code = resolve_ticker_input(ml_defense_ticker)
                    ml_defense_name = get_ticker_name(ml_defense_code)
                    with st.spinner(f"📡 방어 자산 {ml_defense_name} ({ml_defense_code}) 데이터를 불러오는 중..."):
                        ml_defense_df = load_data(start_date, end_date, ml_defense_code)
                    if ml_defense_df is None or ml_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                ml_df = run_ml_backtest(
                    df,
                    pred_series,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=ml_defense_df,
                    defensive_mode=ml_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=ml_defense_code.strip().upper(),
                )
                strategy_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(ml_df['Buy_Signal'] & (~ml_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(ml_df)"""

if old_ml_exec in content:
    content = content.replace(old_ml_exec, new_ml_exec)
    print("Updated ML exec.")

# VBT
old_vbt_exec = """            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                vbt_df = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = vbt_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = vbt_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(vbt_df['Buy_Signal'] & (~vbt_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(vbt_df)"""

new_vbt_exec = """            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                # [LOG: 20260608_1026] 변동성 돌파 전략 방어자산 데이터 로드 및 적용
                vbt_defense_df = None
                vbt_defense_code = "CASH"
                if vbt_defensive_mode == "방어자산":
                    vbt_defense_code = resolve_ticker_input(vbt_defense_ticker)
                    vbt_defense_name = get_ticker_name(vbt_defense_code)
                    with st.spinner(f"📡 방어 자산 {vbt_defense_name} ({vbt_defense_code}) 데이터를 불러오는 중..."):
                        vbt_defense_df = load_data(start_date, end_date, vbt_defense_code)
                    if vbt_defense_df is None or vbt_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                vbt_df = run_vbt_backtest(
                    df,
                    K,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=vbt_defense_df,
                    defensive_mode=vbt_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=vbt_defense_code.strip().upper(),
                )
                strategy_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = vbt_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = vbt_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(vbt_df['Buy_Signal'] & (~vbt_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(vbt_df)"""

if old_vbt_exec in content:
    content = content.replace(old_vbt_exec, new_vbt_exec)
    print("Updated VBT exec.")

# MA Cross
old_ma_exec = """            elif strategy_choice == "이동평균선 골든크로스 전략":
                ma_df = run_ma_cross_backtest(df, ma_short, ma_long, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = ma_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ma_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ma_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ma_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(ma_df['Buy_Signal'] & (~ma_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(ma_df)"""

new_ma_exec = """            elif strategy_choice == "이동평균선 골든크로스 전략":
                # [LOG: 20260608_1027] 이동평균선 골든크로스 전략 방어자산 데이터 로드 및 적용
                ma_defense_df = None
                ma_defense_code = "CASH"
                if ma_defensive_mode == "방어자산":
                    ma_defense_code = resolve_ticker_input(ma_defense_ticker)
                    ma_defense_name = get_ticker_name(ma_defense_code)
                    with st.spinner(f"📡 방어 자산 {ma_defense_name} ({ma_defense_code}) 데이터를 불러오는 중..."):
                        ma_defense_df = load_data(start_date, end_date, ma_defense_code)
                    if ma_defense_df is None or ma_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                ma_df = run_ma_cross_backtest(
                    df,
                    ma_short,
                    ma_long,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=ma_defense_df,
                    defensive_mode=ma_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=ma_defense_code.strip().upper(),
                )
                strategy_final_return = ma_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ma_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ma_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ma_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(ma_df['Buy_Signal'] & (~ma_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(ma_df)"""

if old_ma_exec in content:
    content = content.replace(old_ma_exec, new_ma_exec)
    print("Updated MA exec.")

# RSI
old_rsi_exec = """            elif strategy_choice == "RSI 과매도 반등 전략":
                rsi_df = run_rsi_backtest(df, rsi_period, buy_rsi, sell_rsi, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = rsi_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = rsi_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = rsi_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = rsi_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(rsi_df['Buy_Signal'] & (~rsi_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(rsi_df)"""

new_rsi_exec = """            elif strategy_choice == "RSI 과매도 반등 전략":
                # [LOG: 20260608_1028] RSI 과매도 반등 전략 방어자산 데이터 로드 및 적용
                rsi_defense_df = None
                rsi_defense_code = "CASH"
                if rsi_defensive_mode == "방어자산":
                    rsi_defense_code = resolve_ticker_input(rsi_defense_ticker)
                    rsi_defense_name = get_ticker_name(rsi_defense_code)
                    with st.spinner(f"📡 방어 자산 {rsi_defense_name} ({rsi_defense_code}) 데이터를 불러오는 중..."):
                        rsi_defense_df = load_data(start_date, end_date, rsi_defense_code)
                    if rsi_defense_df is None or rsi_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                rsi_df = run_rsi_backtest(
                    df,
                    rsi_period,
                    buy_rsi,
                    sell_rsi,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=rsi_defense_df,
                    defensive_mode=rsi_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=rsi_defense_code.strip().upper(),
                )
                strategy_final_return = rsi_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = rsi_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = rsi_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = rsi_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(rsi_df['Buy_Signal'] & (~rsi_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(rsi_df)"""

if old_rsi_exec in content:
    content = content.replace(old_rsi_exec, new_rsi_exec)
    print("Updated RSI exec.")

# Bollinger
old_bb_exec = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                bb_df = run_bollinger_backtest(df, bb_period, bb_std, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = bb_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = bb_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = bb_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(bb_df['Buy_Signal'] & (~bb_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(bb_df)"""

new_bb_exec = """            elif strategy_choice == "볼린저 밴드 반등 전략":
                # [LOG: 20260608_1029] 볼린저 밴드 반등 전략 방어자산 데이터 로드 및 적용
                bb_defense_df = None
                bb_defense_code = "CASH"
                if bb_defensive_mode == "방어자산":
                    bb_defense_code = resolve_ticker_input(bb_defense_ticker)
                    bb_defense_name = get_ticker_name(bb_defense_code)
                    with st.spinner(f"📡 방어 자산 {bb_defense_name} ({bb_defense_code}) 데이터를 불러오는 중..."):
                        bb_defense_df = load_data(start_date, end_date, bb_defense_code)
                    if bb_defense_df is None or bb_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                bb_df = run_bollinger_backtest(
                    df,
                    bb_period,
                    bb_std,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=bb_defense_df,
                    defensive_mode=bb_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=bb_defense_code.strip().upper(),
                )
                strategy_final_return = bb_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = bb_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = bb_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(bb_df['Buy_Signal'] & (~bb_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(bb_df)"""

if old_bb_exec in content:
    content = content.replace(old_bb_exec, new_bb_exec)
    print("Updated BB exec.")

# MACD
old_macd_exec = """            # MACD 추세 연산
            elif strategy_choice == "MACD 추세 전략":
                macd_df = run_macd_backtest(df, macd_fast, macd_slow, macd_signal, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = macd_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = macd_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = macd_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = macd_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(macd_df['Buy_Signal'] & (~macd_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(macd_df)"""

new_macd_exec = """            # MACD 추세 연산
            elif strategy_choice == "MACD 추세 전략":
                # [LOG: 20260608_1030] MACD 추세 전략 방어자산 데이터 로드 및 적용
                macd_defense_df = None
                macd_defense_code = "CASH"
                if macd_defensive_mode == "방어자산":
                    macd_defense_code = resolve_ticker_input(macd_defense_ticker)
                    macd_defense_name = get_ticker_name(macd_defense_code)
                    with st.spinner(f"📡 방어 자산 {macd_defense_name} ({macd_defense_code}) 데이터를 불러오는 중..."):
                        macd_defense_df = load_data(start_date, end_date, macd_defense_code)
                    if macd_defense_df is None or macd_defense_df.empty:
                        st.error("❌ 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()
                macd_df = run_macd_backtest(
                    df,
                    macd_fast,
                    macd_slow,
                    macd_signal,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=macd_defense_df,
                    defensive_mode=macd_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=macd_defense_code.strip().upper(),
                )
                strategy_final_return = macd_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = macd_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = macd_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = macd_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(macd_df['Buy_Signal'] & (~macd_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(macd_df)"""

if old_macd_exec in content:
    content = content.replace(old_macd_exec, new_macd_exec)
    print("Updated MACD exec.")

# Combined Comparison Mode
old_combined_exec = """            # 통합 비교 모드 연산 (두 개 모두 연산)
            else:
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                
                # 1. 머신러닝 예측 백테스트
                ml_df_predicted = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate, use_drip)"""

new_combined_exec = """            # 통합 비교 모드 연산 (두 개 모두 연산)
            else:
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                
                # [LOG: 20260608_1030] 통합 비교 모드에서의 ML/VBT 방어 자산 로드
                ml_defense_df = None
                ml_defense_code = "CASH"
                if ml_defensive_mode == "방어자산":
                    ml_defense_code = resolve_ticker_input(ml_defense_ticker)
                    ml_defense_name = get_ticker_name(ml_defense_code)
                    with st.spinner(f"📡 머신러닝 방어 자산 {ml_defense_name} ({ml_defense_code}) 데이터를 불러오는 중..."):
                        ml_defense_df = load_data(start_date, end_date, ml_defense_code)
                    if ml_defense_df is None or ml_defense_df.empty:
                        st.error("❌ 머신러닝 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()

                vbt_defense_df = None
                vbt_defense_code = "CASH"
                if vbt_defensive_mode == "방어자산":
                    vbt_defense_code = resolve_ticker_input(vbt_defense_ticker)
                    vbt_defense_name = get_ticker_name(vbt_defense_code)
                    with st.spinner(f"📡 변동성돌파 방어 자산 {vbt_defense_name} ({vbt_defense_code}) 데이터를 불러오는 중..."):
                        vbt_defense_df = load_data(start_date, end_date, vbt_defense_code)
                    if vbt_defense_df is None or vbt_defense_df.empty:
                        st.error("❌ 변동성돌파 방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                        st.stop()

                # 1. 머신러닝 예측 백테스트
                ml_df_predicted = run_ml_backtest(
                    df,
                    pred_series,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=ml_defense_df,
                    defensive_mode=ml_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=ml_defense_code.strip().upper(),
                )"""

if old_combined_exec in content:
    content = content.replace(old_combined_exec, new_combined_exec)
    print("Updated combined comparison mode exec part 1.")

old_combined_vbt = """                # 3. 변동성 돌파도 전체 기간으로 사용
                vbt_df = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate, use_drip)"""

new_combined_vbt = """                # 3. 변동성 돌파도 전체 기간으로 사용
                vbt_df = run_vbt_backtest(
                    df,
                    K,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    use_drip,
                    defense_df=vbt_defense_df,
                    defensive_mode=vbt_defensive_mode,
                    attack_label=ticker_symbol,
                    defense_label=vbt_defense_code.strip().upper(),
                )"""

if old_combined_vbt in content:
    content = content.replace(old_combined_vbt, new_combined_vbt)
    print("Updated combined comparison mode exec part 2.")


# 6. Add Plotly position markers (Diamond shape) for transitions
# ML Chart
old_ml_chart = """                st.plotly_chart(fig_price, use_container_width=True)"""
# Wait, st.plotly_chart(fig_price, use_container_width=True) is used in multiple places, so we must match with context!
# Let's locate the exact ML chart section
old_ml_chart_block = """                st.subheader(f"🔮 실제 {ticker_name} 종가 vs 예측 주가 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
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

new_ml_chart_block = """                st.subheader(f"🔮 실제 {ticker_name} 종가 vs 예측 주가 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                # [LOG: 20260608_1035] 머신러닝 전략 포지션 전환 마커 추가
                position_markers = ml_df[ml_df['Position'] != ml_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['Actual_Close'],
                    mode="markers",
                    name="포지션 전환",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=position_markers['Selected_Asset'],
                    hovertemplate='<b>포지션 전환</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
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

if old_ml_chart_block in content:
    content = content.replace(old_ml_chart_block, new_ml_chart_block)
    print("Updated ML chart.")

# VBT Chart
old_vbt_chart_block = """            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                st.subheader(f"🏷️ 실제 {ticker_name} 주가 vs 매수 목표가(Buy Target)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="매수 목표가 (시가 + Range * K)", 
                    line=dict(color="#d62728", width=1.5, dash="dash"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
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

new_vbt_chart_block = """            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                st.subheader(f"🏷️ 실제 {ticker_name} 주가 vs 매수 목표가(Buy Target)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="매수 목표가 (시가 + Range * K)", 
                    line=dict(color="#d62728", width=1.5, dash="dash"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
                # [LOG: 20260608_1036] 변동성 돌파 전략 포지션 전환 마커 추가
                position_markers = vbt_df[vbt_df['Position'] != vbt_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['종가'],
                    mode="markers",
                    name="포지션 전환",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=position_markers['Selected_Asset'],
                    hovertemplate='<b>포지션 전환</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
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

if old_vbt_chart_block in content:
    content = content.replace(old_vbt_chart_block, new_vbt_chart_block)
    print("Updated VBT chart.")

# MA Cross Chart
old_ma_chart_block = """            elif strategy_choice == "이동평균선 골든크로스 전략":
                st.subheader(f"📈 실제 {ticker_name} 주가 및 이동평균선(SMA)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Short'], name=f"단기 SMA ({ma_short}일)", 
                    line=dict(color="#ff7f0e", width=1.5),
                    hovertemplate='<b>단기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Long'], name=f"장기 SMA ({ma_long}일)", 
                    line=dict(color="#2ca02c", width=1.5),
                    hovertemplate='<b>장기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
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

new_ma_chart_block = """            elif strategy_choice == "이동평균선 골든크로스 전략":
                st.subheader(f"📈 실제 {ticker_name} 주가 및 이동평균선(SMA)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Short'], name=f"단기 SMA ({ma_short}일)", 
                    line=dict(color="#ff7f0e", width=1.5),
                    hovertemplate='<b>단기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Long'], name=f"장기 SMA ({ma_long}일)", 
                    line=dict(color="#2ca02c", width=1.5),
                    hovertemplate='<b>장기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                # [LOG: 20260608_1037] 이동평균 크로스 전략 포지션 전환 마커 추가
                position_markers = ma_df[ma_df['Position'] != ma_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['종가'],
                    mode="markers",
                    name="포지션 전환",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=position_markers['Selected_Asset'],
                    hovertemplate='<b>포지션 전환</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
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

if old_ma_chart_block in content:
    content = content.replace(old_ma_chart_block, new_ma_chart_block)
    print("Updated MA chart.")

# RSI Chart
old_rsi_chart_block = """            elif strategy_choice == "RSI 과매도 반등 전략":
                st.subheader(f"🔄 실제 {ticker_name} 주가 및 RSI 보조지표")
                
                # 1. 주가 차트
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['종가'], name="실제 종가", 
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
                st.plotly_chart(fig_price, use_container_width=True)"""

new_rsi_chart_block = """            elif strategy_choice == "RSI 과매도 반등 전략":
                st.subheader(f"🔄 실제 {ticker_name} 주가 및 RSI 보조지표")
                
                # 1. 주가 차트
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                # [LOG: 20260608_1038] RSI 전략 포지션 전환 마커 추가
                position_markers = rsi_df[rsi_df['Position'] != rsi_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['종가'],
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
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)"""

if old_rsi_chart_block in content:
    content = content.replace(old_rsi_chart_block, new_rsi_chart_block)
    print("Updated RSI chart.")

# Bollinger Chart
old_bb_chart_block = """            elif strategy_choice == "볼린저 밴드 반등 전략":
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

new_bb_chart_block = """            elif strategy_choice == "볼린저 밴드 반등 전략":
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
                # [LOG: 20260608_1039] 볼린저 밴드 전략 포지션 전환 마커 추가
                position_markers = bb_df[bb_df['Position'] != bb_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['종가'],
                    mode="markers",
                    name="포지션 전환",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=position_markers['Selected_Asset'],
                    hovertemplate='<b>포지션 전환</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
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

if old_bb_chart_block in content:
    content = content.replace(old_bb_chart_block, new_bb_chart_block)
    print("Updated BB chart.")

# MACD Chart
old_macd_chart_block = """            elif strategy_choice == "MACD 추세 전략":
                st.subheader(f"📊 실제 {ticker_name} 주가 및 MACD 신호 지표")
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
                st.plotly_chart(fig_price, use_container_width=True)"""

new_macd_chart_block = """            elif strategy_choice == "MACD 추세 전략":
                st.subheader(f"📊 실제 {ticker_name} 주가 및 MACD 신호 지표")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['종가'], name="실제 종가",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                # [LOG: 20260608_1040] MACD 전략 포지션 전환 마커 추가
                position_markers = macd_df[macd_df['Position'] != macd_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=position_markers.index,
                    y=position_markers['종가'],
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
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)"""

if old_macd_chart_block in content:
    content = content.replace(old_macd_chart_block, new_macd_chart_block)
    print("Updated MACD chart.")


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Finished patching stock_prediction_dashboard.py.")
