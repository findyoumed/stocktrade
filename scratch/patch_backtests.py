import os
import re

filepath = r"d:\work\stocktrade\chapter3\backtest_engine.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Restore from git first to start clean
os.system(f"git checkout {filepath}")

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. run_generic_backtest_with_defense & run_ml_backtest
orig_ml = """def run_ml_backtest(df, pred_series, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다.\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    backtest_df = pd.DataFrame({
        'Actual_Close': df['종가'].loc[pred_series.index],
        'Predicted_Close': pred_series,
        'Prev_Close': df['종가'].shift(1).loc[pred_series.index],
        '배당금': df['배당금'].loc[pred_series.index] if '배당금' in df.columns else 0.0
    }).dropna()
    
    backtest_df['Buy_Signal'] = backtest_df['Predicted_Close'] > backtest_df['Prev_Close']
    prev_signals = backtest_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((backtest_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)
    total_cost = entry_cost + exit_cost
    
    if use_drip and '배당금' in backtest_df.columns:
        div_yield = backtest_df['배당금'] / backtest_df['Prev_Close']
        strategy_div_yield = np.where(backtest_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
    
    backtest_df['Strategy_Return'] = np.where(
        backtest_df['Buy_Signal'],
        (backtest_df['Actual_Close'] / backtest_df['Prev_Close']) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    
    hold_returns = (backtest_df['Actual_Close'] / backtest_df['Prev_Close']) + div_yield
    hold_returns_array = hold_returns.values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    backtest_df['Hold_Return'] = hold_returns_array
    
    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    
    backtest_df['Strategy_Balance'] = initial_budget * backtest_df['Strategy_Return'].cumprod()
    backtest_df['Hold_Balance'] = initial_budget * backtest_df['Hold_Return'].cumprod()
    
    return backtest_df"""

repl_ml = """def run_generic_backtest_with_defense(
    df,
    buy_signals,
    initial_budget,
    fee_rate_pct,
    slippage_rate_pct,
    use_drip=False,
    defense_df=None,
    defensive_mode="현금",
    attack_label="ATTACK",
    defense_label="DEFENSE",
):
    \"\"\"[LOG: 20260608_1007] 개별 단일 자산 전략들을 위한 공통 대피/방어자산 백테스트 엔진\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    backtest_df = df.copy()
    backtest_df['Buy_Signal'] = buy_signals
    
    # Align dates
    if defense_df is not None and defensive_mode == "방어자산":
        def_df = defense_df.copy().sort_index()
        def_close = def_df['종가'].reindex(backtest_df.index).ffill().bfill()
        def_div = def_df['배당금'].reindex(backtest_df.index).fillna(0.0) if '배당금' in def_df.columns else pd.Series(0.0, index=backtest_df.index)
        defense_div_yield = def_div / def_close.shift(1).fillna(def_close)
        defense_return = (def_close / def_close.shift(1).fillna(def_close)).fillna(1.0) + (defense_div_yield if use_drip else 0.0).fillna(0.0)
    else:
        defense_return = pd.Series(1.0, index=backtest_df.index)

    # Position
    backtest_df['Position'] = np.where(backtest_df['Buy_Signal'], "ATTACK", "DEFENSE")
    if defensive_mode == "현금":
        backtest_df['Position'] = np.where(backtest_df['Buy_Signal'], "ATTACK", "CASH")

    # Transitions and cost
    prev_position = backtest_df['Position'].shift(1).fillna("CASH")
    changed = backtest_df['Position'] != prev_position
    
    conds = [
        ~changed,
        (prev_position == "ATTACK") & (backtest_df['Position'] == "CASH"),
        (prev_position == "ATTACK") & (backtest_df['Position'] == "DEFENSE"),
        (prev_position == "DEFENSE") & (backtest_df['Position'] == "ATTACK"),
        (prev_position == "CASH") & (backtest_df['Position'] == "ATTACK"),
        (prev_position == "CASH") & (backtest_df['Position'] == "DEFENSE"),
    ]
    outputs = [
        0.0,
        cost_rate + 0.18 / 100,
        2 * cost_rate + 0.18 / 100,
        2 * cost_rate + 0.18 / 100,
        cost_rate,
        cost_rate,
    ]
    backtest_df['Trade_Cost'] = np.select(conds, outputs, default=2 * cost_rate + 0.18 / 100)

    # Asset return
    attack_div_yield = backtest_df['배당금'] / backtest_df['종가'].shift(1).fillna(backtest_df['종가']) if '배당금' in backtest_df.columns else 0.0
    attack_return = (backtest_df['종가'] / backtest_df['종가'].shift(1).fillna(backtest_df['종가'])).fillna(1.0) + (attack_div_yield if use_drip else 0.0).fillna(0.0)

    backtest_df['Gross_Strategy_Return'] = np.select(
        [
            backtest_df['Position'] == "ATTACK",
            backtest_df['Position'] == "DEFENSE",
        ],
        [
            attack_return,
            defense_return,
        ],
        default=1.0,
    )

    backtest_df['Strategy_Return'] = (backtest_df['Gross_Strategy_Return'] - backtest_df['Trade_Cost']).clip(lower=0)
    backtest_df['Strategy_Return'] = backtest_df['Strategy_Return'].fillna(1.0)
    
    # Hold Return
    hold_returns = attack_return.fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    backtest_df['Hold_Return'] = hold_returns

    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    backtest_df['Strategy_Balance'] = initial_budget * backtest_df['Strategy_Return'].cumprod()
    backtest_df['Hold_Balance'] = initial_budget * backtest_df['Hold_Return'].cumprod()
    backtest_df['Daily_Return_Pct'] = (backtest_df['Strategy_Return'] - 1) * 100
    
    backtest_df['Selected_Asset'] = backtest_df['Position'].map({
        "ATTACK": attack_label,
        "DEFENSE": defense_label,
        "CASH": "현금",
    })
    
    return backtest_df

def run_ml_backtest(df, pred_series, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다.\"\"\"
    backtest_df = pd.DataFrame({
        '종가': df['종가'].loc[pred_series.index],
        'Prev_Close': df['종가'].shift(1).loc[pred_series.index],
        '배당금': df['배당금'].loc[pred_series.index] if '배당금' in df.columns else 0.0
    }).dropna()
    
    buy_signals = pred_series.loc[backtest_df.index] > backtest_df['Prev_Close']
    
    res_df = run_generic_backtest_with_defense(
        df=backtest_df,
        buy_signals=buy_signals,
        initial_budget=initial_budget,
        fee_rate_pct=fee_rate_pct,
        slippage_rate_pct=slippage_rate_pct,
        use_drip=use_drip,
        defense_df=defense_df,
        defensive_mode=defensive_mode,
        attack_label=attack_label,
        defense_label=defense_label
    )
    res_df['Actual_Close'] = res_df['종가']
    res_df['Predicted_Close'] = pred_series.loc[res_df.index]
    return res_df"""

# 2. run_vbt_backtest (regex matching)
repl_vbt = """def run_vbt_backtest(df, K, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"변동성 돌파 전략 백테스트를 수행합니다.\"\"\"
    # [LOG: 20260605_0950]
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    vbt_df = df.copy()
    
    # OHLC 데이터 검증 (고가와 저가가 95% 이상 같은지 체크하여 종가만 채워진 부실 데이터 판별)
    is_invalid_ohlc = (vbt_df['고가'] == vbt_df['저가']).mean() > 0.95
    if is_invalid_ohlc:
        st.session_state['vbt_warning'] = "⚠️ 경고: 현재 종목 데이터는 시가/고가/저가가 누락되어 종가로 채워진 '간소화/변형 버전' 데이터입니다. 래리 윌리엄스의 변동성 돌파 전략이 정상적으로 작동하지 않을 수 있습니다."
    else:
        st.session_state['vbt_warning'] = None
        
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    # 실제 매수 체결 가격 계산 (당일 시가 > 목표가인 갭상승의 경우 시가에 체결)
    vbt_df['Buy_Price'] = np.where(
        vbt_df['시가'] > vbt_df['Buy_Target'],
        vbt_df['시가'],
        vbt_df['Buy_Target']
    )
    
    # [LOG: 20260605_1020] 배당금 재투자 (DRIP) 반영 조건 설정
    if use_drip and '배당금' in vbt_df.columns:
        div_yield = vbt_df['배당금'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])
        strategy_div_yield = np.where(vbt_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0

    if defense_df is not None and defensive_mode == "방어자산":
        def_df = defense_df.copy().sort_index()
        def_close = def_df['종가'].reindex(vbt_df.index).ffill().bfill()
        def_div = def_df['배당금'].reindex(vbt_df.index).fillna(0.0) if '배당금' in def_df.columns else pd.Series(0.0, index=vbt_df.index)
        defense_div_yield = def_div / def_close.shift(1).fillna(def_close)
        defense_return = (def_close / def_close.shift(1).fillna(def_close)).fillna(1.0) + (defense_div_yield if use_drip else 0.0).fillna(0.0)
        
        # Breakout day return: we sell Defense, buy Attack, sell Attack, buy Defense.
        # Total cost is 4 * cost_rate + 0.36/100
        breakout_return = (vbt_df['종가'] / vbt_df['Buy_Price']) + strategy_div_yield - (4 * cost_rate + 0.36 / 100)
        
        vbt_df['Strategy_Return'] = np.where(
            vbt_df['Buy_Signal'],
            breakout_return,
            defense_return
        )
        vbt_df['Position'] = np.where(vbt_df['Buy_Signal'], "ATTACK", "DEFENSE")
    else:
        # Cash mode
        breakout_return = (vbt_df['종가'] / vbt_df['Buy_Price']) + strategy_div_yield - (2 * cost_rate + 0.18 / 100)
        vbt_df['Strategy_Return'] = np.where(
            vbt_df['Buy_Signal'],
            breakout_return,
            1.0
        )
        vbt_df['Position'] = np.where(vbt_df['Buy_Signal'], "ATTACK", "CASH")
        
    vbt_df['Strategy_Return'] = vbt_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (vbt_df['종가'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    vbt_df['Hold_Return'] = hold_returns_array
    
    vbt_df['Strategy_Cum_Return'] = (vbt_df['Strategy_Return'].cumprod() - 1) * 100
    vbt_df['Hold_Cum_Return'] = (vbt_df['Hold_Return'].cumprod() - 1) * 100
    
    vbt_df['Strategy_Balance'] = initial_budget * vbt_df['Strategy_Return'].cumprod()
    vbt_df['Hold_Balance'] = initial_budget * vbt_df['Hold_Return'].cumprod()
    vbt_df['Daily_Return_Pct'] = (vbt_df['Strategy_Return'] - 1) * 100
    
    vbt_df['Selected_Asset'] = vbt_df['Position'].map({
        "ATTACK": attack_label,
        "DEFENSE": defense_label,
        "CASH": "현금",
    })
    
    return vbt_df"""

# 3. run_ma_cross_backtest
orig_ma = """def run_ma_cross_backtest(df, short_period, long_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"이동평균선 골든크로스 전략 백테스트 함수\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    ma_df = df.copy()
    ma_df['SMA_Short'] = ma_df['종가'].rolling(window=short_period).mean()
    ma_df['SMA_Long'] = ma_df['종가'].rolling(window=long_period).mean()
    
    ma_df['Buy_Signal'] = ma_df['SMA_Short'] > ma_df['SMA_Long']
    ma_df['Buy_Signal'] = np.where(pd.isna(ma_df['SMA_Long']), False, ma_df['Buy_Signal'])
    
    prev_signals = ma_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((ma_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((ma_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)
    total_cost = entry_cost + exit_cost
    
    if use_drip and '배당금' in ma_df.columns:
        div_yield = ma_df['배당금'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])
        strategy_div_yield = np.where(ma_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    ma_df['Strategy_Return'] = np.where(
        ma_df['Buy_Signal'],
        (ma_df['종가'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    ma_df['Strategy_Return'] = ma_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (ma_df['종가'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    ma_df['Hold_Return'] = hold_returns_array
    
    ma_df['Strategy_Cum_Return'] = (ma_df['Strategy_Return'].cumprod() - 1) * 100
    ma_df['Hold_Cum_Return'] = (ma_df['Hold_Return'].cumprod() - 1) * 100
    ma_df['Strategy_Balance'] = initial_budget * ma_df['Strategy_Return'].cumprod()
    ma_df['Hold_Balance'] = initial_budget * ma_df['Hold_Return'].cumprod()
    
    ma_df['Daily_Return_Pct'] = (ma_df['Strategy_Return'] - 1) * 100
    return ma_df"""

repl_ma = """def run_ma_cross_backtest(df, short_period, long_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"이동평균선 골든크로스 전략 백테스트 함수\"\"\"
    ma_df = df.copy()
    ma_df['SMA_Short'] = ma_df['종가'].rolling(window=short_period).mean()
    ma_df['SMA_Long'] = ma_df['종가'].rolling(window=long_period).mean()
    
    buy_signals = ma_df['SMA_Short'] > ma_df['SMA_Long']
    buy_signals = np.where(pd.isna(ma_df['SMA_Long']), False, buy_signals)
    
    res_df = run_generic_backtest_with_defense(
        df=ma_df,
        buy_signals=buy_signals,
        initial_budget=initial_budget,
        fee_rate_pct=fee_rate_pct,
        slippage_rate_pct=slippage_rate_pct,
        use_drip=use_drip,
        defense_df=defense_df,
        defensive_mode=defensive_mode,
        attack_label=attack_label,
        defense_label=defense_label
    )
    res_df['SMA_Short'] = ma_df['SMA_Short']
    res_df['SMA_Long'] = ma_df['SMA_Long']
    return res_df"""

# 4. run_rsi_backtest
orig_rsi = """def run_rsi_backtest(df, period, buy_rsi, sell_rsi, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"RSI 과매도 반등 전략 백테스트 함수\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    rsi_df = df.copy()
    delta = rsi_df['종가'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi_df['RSI'] = 100 - (100 / (1 + rs))
    
    signals = []
    position = False
    for r in rsi_df['RSI'].values:
        if pd.isna(r):
            signals.append(False)
        elif not position and r <= buy_rsi:
            position = True
            signals.append(True)
        elif position and r >= sell_rsi:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    rsi_df['Buy_Signal'] = signals
    prev_signals = rsi_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((rsi_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((rsi_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)
    total_cost = entry_cost + exit_cost
    
    if use_drip and '배당금' in rsi_df.columns:
        div_yield = rsi_df['배당금'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])
        strategy_div_yield = np.where(rsi_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    rsi_df['Strategy_Return'] = np.where(
        rsi_df['Buy_Signal'],
        (rsi_df['종가'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    rsi_df['Strategy_Return'] = rsi_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (rsi_df['종가'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    rsi_df['Hold_Return'] = hold_returns_array
    
    rsi_df['Strategy_Cum_Return'] = (rsi_df['Strategy_Return'].cumprod() - 1) * 100
    rsi_df['Hold_Cum_Return'] = (rsi_df['Hold_Return'].cumprod() - 1) * 100
    rsi_df['Strategy_Balance'] = initial_budget * rsi_df['Strategy_Return'].cumprod()
    rsi_df['Hold_Balance'] = initial_budget * rsi_df['Hold_Return'].cumprod()
    
    rsi_df['Daily_Return_Pct'] = (rsi_df['Strategy_Return'] - 1) * 100
    return rsi_df"""

repl_rsi = """def run_rsi_backtest(df, period, buy_rsi, sell_rsi, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"RSI 과매도 반등 전략 백테스트 함수\"\"\"
    rsi_df = df.copy()
    delta = rsi_df['종가'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi_df['RSI'] = 100 - (100 / (1 + rs))
    
    signals = []
    position = False
    for r in rsi_df['RSI'].values:
        if pd.isna(r):
            signals.append(False)
        elif not position and r <= buy_rsi:
            position = True
            signals.append(True)
        elif position and r >= sell_rsi:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    buy_signals = pd.Series(signals, index=rsi_df.index)
    
    res_df = run_generic_backtest_with_defense(
        df=rsi_df,
        buy_signals=buy_signals,
        initial_budget=initial_budget,
        fee_rate_pct=fee_rate_pct,
        slippage_rate_pct=slippage_rate_pct,
        use_drip=use_drip,
        defense_df=defense_df,
        defensive_mode=defensive_mode,
        attack_label=attack_label,
        defense_label=defense_label
    )
    res_df['RSI'] = rsi_df['RSI']
    return res_df"""

# 5. run_bollinger_backtest
orig_bb = """def run_bollinger_backtest(df, period, std_dev, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"볼린저 밴드 반등 전략 백테스트 함수\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    bb_df = df.copy()
    bb_df['Mid'] = bb_df['종가'].rolling(window=period).mean()
    bb_df['Std'] = bb_df['종가'].rolling(window=period).std()
    bb_df['Upper_Band'] = bb_df['Mid'] + (std_dev * bb_df['Std'])
    bb_df['Lower_Band'] = bb_df['Mid'] - (std_dev * bb_df['Std'])
    
    signals = []
    position = False
    closes = bb_df['종가'].values
    lowers = bb_df['Lower_Band'].values
    uppers = bb_df['Upper_Band'].values
    
    for i in range(len(bb_df)):
        c = closes[i]
        l = lowers[i]
        u = uppers[i]
        if pd.isna(l) or pd.isna(u):
            signals.append(False)
        elif not position and c <= l:
            position = True
            signals.append(True)
        elif position and c >= u:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    bb_df['Buy_Signal'] = signals
    prev_signals = bb_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((bb_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((bb_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)
    total_cost = entry_cost + exit_cost
    
    if use_drip and '배당금' in bb_df.columns:
        div_yield = bb_df['배당금'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])
        strategy_div_yield = np.where(bb_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    bb_df['Strategy_Return'] = np.where(
        bb_df['Buy_Signal'],
        (bb_df['종가'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    bb_df['Strategy_Return'] = bb_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (bb_df['종가'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    bb_df['Hold_Return'] = hold_returns_array
    
    bb_df['Strategy_Cum_Return'] = (bb_df['Strategy_Return'].cumprod() - 1) * 100
    bb_df['Hold_Cum_Return'] = (bb_df['Hold_Return'].cumprod() - 1) * 100
    bb_df['Strategy_Balance'] = initial_budget * bb_df['Strategy_Return'].cumprod()
    bb_df['Hold_Balance'] = initial_budget * bb_df['Hold_Return'].cumprod()
    
    bb_df['Daily_Return_Pct'] = (bb_df['Strategy_Return'] - 1) * 100
    return bb_df"""

repl_bb = """def run_bollinger_backtest(df, period, std_dev, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"볼린저 밴드 반등 전략 백테스트 함수\"\"\"
    bb_df = df.copy()
    bb_df['Mid'] = bb_df['종가'].rolling(window=period).mean()
    bb_df['Std'] = bb_df['종가'].rolling(window=period).std()
    bb_df['Upper_Band'] = bb_df['Mid'] + (std_dev * bb_df['Std'])
    bb_df['Lower_Band'] = bb_df['Mid'] - (std_dev * bb_df['Std'])
    
    signals = []
    position = False
    closes = bb_df['종가'].values
    lowers = bb_df['Lower_Band'].values
    uppers = bb_df['Upper_Band'].values
    
    for i in range(len(bb_df)):
        c = closes[i]
        l = lowers[i]
        u = uppers[i]
        if pd.isna(l) or pd.isna(u):
            signals.append(False)
        elif not position and c <= l:
            position = True
            signals.append(True)
        elif position and c >= u:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    buy_signals = pd.Series(signals, index=bb_df.index)
    
    res_df = run_generic_backtest_with_defense(
        df=bb_df,
        buy_signals=buy_signals,
        initial_budget=initial_budget,
        fee_rate_pct=fee_rate_pct,
        slippage_rate_pct=slippage_rate_pct,
        use_drip=use_drip,
        defense_df=defense_df,
        defensive_mode=defensive_mode,
        attack_label=attack_label,
        defense_label=defense_label
    )
    res_df['Mid'] = bb_df['Mid']
    res_df['Upper_Band'] = bb_df['Upper_Band']
    res_df['Lower_Band'] = bb_df['Lower_Band']
    return res_df"""

# 6. run_macd_backtest
orig_macd = """def run_macd_backtest(df, fast_period=12, slow_period=26, signal_period=9, initial_budget=10000000, fee_rate_pct=0.15, slippage_rate_pct=0.10, use_drip=False):
    \"\"\"MACD 추세 전략 백테스트를 수행합니다.\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    macd_df = df.copy()
    
    # 지수이동평균(EMA)을 기반으로 MACD 지표 산출
    ema_fast = macd_df['종가'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = macd_df['종가'].ewm(span=slow_period, adjust=False).mean()
    macd_df['MACD'] = ema_fast - ema_slow
    macd_df['Signal'] = macd_df['MACD'].ewm(span=signal_period, adjust=False).mean()
    macd_df['Histogram'] = macd_df['MACD'] - macd_df['Signal']
    
    # 매수 조건: MACD선이 Signal선 위에 있을 때 보유 유지
    raw_signal = macd_df['MACD'] > macd_df['Signal']
    raw_signal = np.where(pd.isna(macd_df['Signal']), False, raw_signal)
    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    macd_df['Buy_Signal'] = pd.Series(raw_signal, index=macd_df.index).shift(1).fillna(False)
    
    prev_signals = macd_df['Buy_Signal'].shift(1).fillna(False)
    
    # 진입/이탈 거래 비용 반영
    entry_cost = np.where((macd_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((macd_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate + 0.18 / 100, 0.0)
    total_cost = entry_cost + exit_cost
    
    if use_drip and '배당금' in macd_df.columns:
        div_yield = macd_df['배당금'] / macd_df['종가'].shift(1).fillna(macd_df['종가'])
        strategy_div_yield = np.where(macd_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    macd_df['Strategy_Return'] = np.where(
        macd_df['Buy_Signal'],
        (macd_df['종가'] / macd_df['종가'].shift(1).fillna(macd_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    macd_df['Strategy_Return'] = macd_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (macd_df['종가'] / macd_df['종가'].shift(1).fillna(macd_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    macd_df['Hold_Return'] = hold_returns_array
    
    macd_df['Strategy_Cum_Return'] = (macd_df['Strategy_Return'].cumprod() - 1) * 100
    macd_df['Hold_Cum_Return'] = (macd_df['Hold_Return'].cumprod() - 1) * 100
    macd_df['Strategy_Balance'] = initial_budget * macd_df['Strategy_Return'].cumprod()
    macd_df['Hold_Balance'] = initial_budget * macd_df['Hold_Return'].cumprod()
    
    macd_df['Daily_Return_Pct'] = (macd_df['Strategy_Return'] - 1) * 100
    return macd_df"""

repl_macd = """def run_macd_backtest(df, fast_period=12, slow_period=26, signal_period=9, initial_budget=10000000, fee_rate_pct=0.15, slippage_rate_pct=0.10, use_drip=False, defense_df=None, defensive_mode="현금", attack_label="ATTACK", defense_label="DEFENSE"):
    \"\"\"MACD 추세 전략 백테스트를 수행합니다.\"\"\"
    macd_df = df.copy()
    
    # 지수이동평균(EMA)을 기반으로 MACD 지표 산출
    ema_fast = macd_df['종가'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = macd_df['종가'].ewm(span=slow_period, adjust=False).mean()
    macd_df['MACD'] = ema_fast - ema_slow
    macd_df['Signal'] = macd_df['MACD'].ewm(span=signal_period, adjust=False).mean()
    macd_df['Histogram'] = macd_df['MACD'] - macd_df['Signal']
    
    # 매수 조건: MACD선이 Signal선 위에 있을 때 보유 유지
    raw_signal = macd_df['MACD'] > macd_df['Signal']
    raw_signal = np.where(pd.isna(macd_df['Signal']), False, raw_signal)
    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    buy_signals = pd.Series(raw_signal, index=macd_df.index).shift(1).fillna(False)
    
    res_df = run_generic_backtest_with_defense(
        df=macd_df,
        buy_signals=buy_signals,
        initial_budget=initial_budget,
        fee_rate_pct=fee_rate_pct,
        slippage_rate_pct=slippage_rate_pct,
        use_drip=use_drip,
        defense_df=defense_df,
        defensive_mode=defensive_mode,
        attack_label=attack_label,
        defense_label=defense_label
    )
    res_df['MACD'] = macd_df['MACD']
    res_df['Signal'] = macd_df['Signal']
    res_df['Histogram'] = macd_df['Histogram']
    return res_df"""

# Replace ML first
if orig_ml in content:
    content = content.replace(orig_ml, repl_ml)
    print("Replaced ML successfully.")

# Replace VBT using regex to locate exactly
pattern_vbt = r"def run_vbt_backtest[\s\S]+?return vbt_df"
if re.search(pattern_vbt, content):
    content = re.sub(pattern_vbt, repl_vbt, content)
    print("Replaced VBT successfully via regex.")
else:
    print("Failed to find VBT pattern.")

# Replace MA Cross
if orig_ma in content:
    content = content.replace(orig_ma, repl_ma)
    print("Replaced MA successfully.")

# Replace RSI
if orig_rsi in content:
    content = content.replace(orig_rsi, repl_rsi)
    print("Replaced RSI successfully.")

# Replace Bollinger
if orig_bb in content:
    content = content.replace(orig_bb, repl_bb)
    print("Replaced BB successfully.")

# Replace MACD
if orig_macd in content:
    content = content.replace(orig_macd, repl_macd)
    print("Replaced MACD successfully.")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished patching.")
