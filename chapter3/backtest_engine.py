# [LOG: 20260604_1952]
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor

def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

@st.cache_data
def run_rolling_forecast(X, y, window_size):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 종가를 예측합니다."""
    predictions = []
    prediction_dates = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_steps = len(X) - window_size
    
    for i in range(window_size, len(X)):
        X_train = X.iloc[i-window_size:i]
        y_train = y.iloc[i-window_size:i]
        X_test = X.iloc[[i]]
        
        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        pred = model.predict(X_test)[0]
        predictions.append(pred)
        prediction_dates.append(X.index[i])
        
        current_step = i - window_size + 1
        progress_bar.progress(current_step / total_steps)
        status_text.text(f"머신러닝 예측 진행 중: {current_step}/{total_steps} 영업일 완료...")
        
    progress_bar.empty()
    status_text.empty()
    
    pred_series = pd.Series(predictions, index=prediction_dates)
    return pred_series

def run_ml_backtest(df, pred_series, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다."""
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
    exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
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
    
    return backtest_df

def calculate_ml_monthly_stats(actual, predicted, backtest_df):
    """머신러닝 예측 오차 및 월별 수익률 통계를 계산합니다."""
    compare_df = pd.DataFrame({
        'Actual': actual,
        'Predicted': predicted,
        'Strategy_Return': backtest_df['Strategy_Return']
    }).dropna()
    
    compare_df['Absolute Error'] = (compare_df['Actual'] - compare_df['Predicted']).abs()
    compare_df['YearMonth'] = compare_df.index.strftime('%Y-%m')
    
    monthly_mae = compare_df.groupby('YearMonth')['Absolute Error'].mean().reset_index()
    monthly_mae.columns = ['년-월', '평균 절대 오차 (원)']
    
    compare_df['Error Rate (%)'] = (compare_df['Absolute Error'] / compare_df['Actual']) * 100
    monthly_error_rate = compare_df.groupby('YearMonth')['Error Rate (%)'].mean().reset_index()
    monthly_error_rate.columns = ['년-월', '평균 오차율 (%)']
    
    monthly_return = compare_df.groupby('YearMonth')['Strategy_Return'].prod().reset_index()
    monthly_return['Strategy_Return'] = (monthly_return['Strategy_Return'] - 1) * 100
    monthly_return.columns = ['년-월', '월간 수익률 (%)']
    
    stats_df = pd.merge(monthly_mae, monthly_error_rate, on='년-월')
    stats_df = pd.merge(stats_df, monthly_return, on='년-월')
    return stats_df

def run_vbt_backtest(df, K, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """변동성 돌파 전략 백테스트를 수행합니다."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    round_trip_cost = 2 * cost_rate
    
    vbt_df = df.copy()
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        (vbt_df['종가'] / vbt_df['Buy_Target']) - round_trip_cost,
        1.0
    )
    
    if use_drip and '배당금' in vbt_df.columns:
        div_yield = vbt_df['배당금'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])
    else:
        div_yield = 0.0
    
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
    
    return vbt_df

def calculate_vbt_monthly_stats(vbt_df):
    """변동성 돌파 전략의 월간 매수 횟수 및 수익률 통계를 계산합니다."""
    stats_df = vbt_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    
    summary.columns = ['년-월', '매수 횟수 (회)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def calculate_combined_monthly_stats(ml_df, vbt_df):
    """두 전략의 월별 수익률 및 머신러닝 오차율을 하나의 표로 통합하여 요약합니다."""
    ml_df = ml_df.copy()
    ml_df['YearMonth'] = ml_df.index.strftime('%Y-%m')
    ml_df['Absolute Error'] = (ml_df['Actual_Close'] - ml_df['Predicted_Close']).abs()
    
    ml_summary = ml_df.groupby('YearMonth').agg({
        'Absolute Error': 'mean',
        'Strategy_Return': 'prod'
    }).reset_index()
    ml_summary.columns = ['년-월', '머신러닝 오차 (원)', 'ML_Return_Prod']
    
    vbt_df = vbt_df.copy()
    vbt_df['YearMonth'] = vbt_df.index.strftime('%Y-%m')
    vbt_df['Buy_Count'] = np.where(vbt_df['Buy_Signal'], 1, 0)
    
    vbt_summary = vbt_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    vbt_summary.columns = ['년-월', '돌파 매수 횟수 (회)', 'VBT_Return_Prod', 'Hold_Return_Prod']
    
    merged = pd.merge(ml_summary, vbt_summary, on='년-월')
    merged['머신러닝 수익률 (%)'] = (merged['ML_Return_Prod'] - 1) * 100
    merged['변동성 돌파 수익률 (%)'] = (merged['VBT_Return_Prod'] - 1) * 100
    merged['단순 보유 수익률 (%)'] = (merged['Hold_Return_Prod'] - 1) * 100
    
    final_df = merged[['년-월', '머신러닝 수익률 (%)', '변동성 돌파 수익률 (%)', '단순 보유 수익률 (%)', '돌파 매수 횟수 (회)', '머신러닝 오차 (원)']]
    return final_df

def run_ma_cross_backtest(df, short_period, long_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """이동평균선 골든크로스 전략 백테스트 함수"""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    ma_df = df.copy()
    ma_df['SMA_Short'] = ma_df['종가'].rolling(window=short_period).mean()
    ma_df['SMA_Long'] = ma_df['종가'].rolling(window=long_period).mean()
    
    ma_df['Buy_Signal'] = ma_df['SMA_Short'] > ma_df['SMA_Long']
    ma_df['Buy_Signal'] = np.where(pd.isna(ma_df['SMA_Long']), False, ma_df['Buy_Signal'])
    
    prev_signals = ma_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((ma_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((ma_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
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
    return ma_df

def calculate_ma_cross_monthly_stats(ma_df):
    """이동평균 크로스 전략의 월별 통계"""
    ma_df = ma_df.copy()
    ma_df['YearMonth'] = ma_df.index.strftime('%Y-%m')
    ma_df['Buy_Count'] = np.where(ma_df['Buy_Signal'], 1, 0)
    summary = ma_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def run_rsi_backtest(df, period, buy_rsi, sell_rsi, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """RSI 과매도 반등 전략 백테스트 함수"""
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
    exit_cost = np.where((rsi_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
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
    return rsi_df

def calculate_rsi_monthly_stats(rsi_df):
    """RSI 과매도 반등 전략의 월별 통계"""
    rsi_df = rsi_df.copy()
    rsi_df['YearMonth'] = rsi_df.index.strftime('%Y-%m')
    rsi_df['Buy_Count'] = np.where(rsi_df['Buy_Signal'], 1, 0)
    summary = rsi_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def run_bollinger_backtest(df, period, std_dev, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """볼린저 밴드 반등 전략 백테스트 함수"""
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
    exit_cost = np.where((bb_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
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
    return bb_df

def calculate_bb_monthly_stats(bb_df):
    """볼린저 밴드 반등 전략의 월별 통계"""
    bb_df = bb_df.copy()
    bb_df['YearMonth'] = bb_df.index.strftime('%Y-%m')
    bb_df['Buy_Count'] = np.where(bb_df['Buy_Signal'], 1, 0)
    summary = bb_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary
