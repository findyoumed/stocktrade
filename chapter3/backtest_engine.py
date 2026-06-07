# [LOG: 20260604_1952]
# [LOG: 20260607_2234] 적립식 존버 물타기(DCA) 및 200일선+MACD 필터 전략 추가
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

    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        (vbt_df['종가'] * (1 - cost_rate - 0.18 / 100)) / (vbt_df['Buy_Price'] * (1 + cost_rate)) + strategy_div_yield,
        1.0
    )
    
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

def run_dual_momentum_backtest(
    attack_df,
    defense_df,
    attack_label,
    defense_label,
    lookback_days,
    initial_budget,
    fee_rate_pct,
    slippage_rate_pct,
    defensive_mode="방어자산",
    use_drip=False,
):
    """공격 자산과 방어 자산을 월별로 비교해 더 강한 자산에 배분하는 듀얼 모멘텀 전략."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100

    combined = pd.DataFrame({
        'Attack_Close': attack_df['종가'],
        'Defense_Close': defense_df['종가'],
        'Attack_Dividend': attack_df['배당금'] if use_drip and '배당금' in attack_df.columns else 0.0,
        'Defense_Dividend': defense_df['배당금'] if use_drip and '배당금' in defense_df.columns else 0.0,
    }).sort_index().ffill().dropna(subset=['Attack_Close', 'Defense_Close'])

    if combined.empty:
        return combined

    combined['Attack_Momentum'] = combined['Attack_Close'] / combined['Attack_Close'].shift(lookback_days) - 1
    combined['Defense_Momentum'] = combined['Defense_Close'] / combined['Defense_Close'].shift(lookback_days) - 1

    rebalance_dates = combined.groupby(combined.index.to_period('M')).tail(1).index

    combined['Target_Asset'] = pd.Series(index=combined.index, dtype=object)
    for dt in rebalance_dates:
        attack_momentum = combined.at[dt, 'Attack_Momentum']
        defense_momentum = combined.at[dt, 'Defense_Momentum']
        if pd.isna(attack_momentum) or pd.isna(defense_momentum):
            target_asset = "CASH"
        elif attack_momentum > defense_momentum and attack_momentum > 0:
            target_asset = "ATTACK"
        elif defensive_mode == "현금" and defense_momentum <= 0:
            target_asset = "CASH"
        else:
            target_asset = "DEFENSE"
        combined.at[dt, 'Target_Asset'] = target_asset

    combined['Position'] = combined['Target_Asset'].shift(1).ffill().fillna("CASH")

    attack_div_yield = combined['Attack_Dividend'] / combined['Attack_Close'].shift(1).fillna(combined['Attack_Close'])
    defense_div_yield = combined['Defense_Dividend'] / combined['Defense_Close'].shift(1).fillna(combined['Defense_Close'])
    combined['Attack_Return'] = (combined['Attack_Close'] / combined['Attack_Close'].shift(1).fillna(combined['Attack_Close'])) + attack_div_yield
    combined['Defense_Return'] = (combined['Defense_Close'] / combined['Defense_Close'].shift(1).fillna(combined['Defense_Close'])) + defense_div_yield
    combined['Cash_Return'] = 1.0

    combined['Gross_Strategy_Return'] = np.select(
        [
            combined['Position'] == "ATTACK",
            combined['Position'] == "DEFENSE",
        ],
        [
            combined['Attack_Return'],
            combined['Defense_Return'],
        ],
        default=combined['Cash_Return']
    )

    prev_position = combined['Position'].shift(1).fillna("CASH")
    changed = combined['Position'] != prev_position
    conds = [
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
    combined['Trade_Cost'] = np.select(conds, outputs, default=2 * cost_rate)
    combined['Strategy_Return'] = (combined['Gross_Strategy_Return'] - combined['Trade_Cost']).clip(lower=0)

    hold_returns = combined['Attack_Return'].fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    combined['Hold_Return'] = hold_returns

    combined['Strategy_Cum_Return'] = (combined['Strategy_Return'].cumprod() - 1) * 100
    combined['Hold_Cum_Return'] = (combined['Hold_Return'].cumprod() - 1) * 100
    combined['Strategy_Balance'] = initial_budget * combined['Strategy_Return'].cumprod()
    combined['Hold_Balance'] = initial_budget * combined['Hold_Return'].cumprod()
    combined['Daily_Return_Pct'] = (combined['Strategy_Return'] - 1) * 100
    combined['Selected_Asset'] = combined['Position'].map({
        "ATTACK": attack_label,
        "DEFENSE": defense_label,
        "CASH": "현금",
    })
    return combined

def calculate_dual_momentum_monthly_stats(dm_df):
    """듀얼 모멘텀 전략의 월별 수익률과 월말 선택 자산을 요약합니다."""
    stats_df = dm_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    summary = stats_df.groupby('YearMonth').agg({
        'Selected_Asset': 'last',
        'Attack_Momentum': 'last',
        'Defense_Momentum': 'last',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod',
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary['Attack_Momentum'] = summary['Attack_Momentum'] * 100
    summary['Defense_Momentum'] = summary['Defense_Momentum'] * 100
    summary.columns = ['년-월', '선택 자산', '공격 모멘텀 (%)', '방어 모멘텀 (%)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def run_macd_backtest(df, fast_period=12, slow_period=26, signal_period=9, initial_budget=10000000, fee_rate_pct=0.15, slippage_rate_pct=0.10, use_drip=False):
    """MACD 추세 전략 백테스트를 수행합니다."""
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
    return macd_df

def calculate_macd_monthly_stats(macd_df):
    """MACD 추세 전략의 월별 통계"""
    macd_df = macd_df.copy()
    macd_df['YearMonth'] = macd_df.index.strftime('%Y-%m')
    macd_df['Buy_Count'] = np.where(macd_df['Buy_Signal'], 1, 0)
    summary = macd_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def run_sma_macd_filter_backtest(
    attack_df,
    defense_df=None,
    attack_label="QQQ",
    defense_label="TLT",
    sma_period=200,
    fast_period=12,
    slow_period=26,
    signal_period=9,
    initial_budget=10000000,
    fee_rate_pct=0.15,
    slippage_rate_pct=0.10,
    rebalance_frequency="M",
    defensive_mode="방어자산",
    signal_mode="strict",
    use_drip=False,
):
    """200일선과 MACD를 함께 쓰는 추세 필터 전략 백테스트.

    strict 모드는 공격 자산이 장기 추세(종가 > SMA)와 모멘텀(MACD > Signal)을
    모두 만족할 때만 보유합니다. sma_exit 모드는 MACD를 진입 확인용으로만 쓰고,
    진입 후에는 종가가 SMA 아래로 내려갈 때까지 보유합니다.
    신호 산출 당일 종가를 미리 알고 매매하는 미래 참조 편향을 피하기 위해
    실제 포지션은 다음 거래일부터 적용합니다.
    """
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100

    attack = attack_df.copy().sort_index()
    if defense_df is not None:
        defense = defense_df.copy().sort_index()
        combined = pd.DataFrame({
            'Attack_Close': attack['종가'],
            'Defense_Close': defense['종가'],
            'Attack_Dividend': attack['배당금'] if use_drip and '배당금' in attack.columns else 0.0,
            'Defense_Dividend': defense['배당금'] if use_drip and '배당금' in defense.columns else 0.0,
        }).sort_index().ffill().dropna(subset=['Attack_Close', 'Defense_Close'])
    else:
        combined = pd.DataFrame({
            'Attack_Close': attack['종가'],
            'Attack_Dividend': attack['배당금'] if use_drip and '배당금' in attack.columns else 0.0,
        }).sort_index().ffill().dropna(subset=['Attack_Close'])
        combined['Defense_Close'] = np.nan
        combined['Defense_Dividend'] = 0.0

    if combined.empty:
        return combined

    combined['SMA'] = combined['Attack_Close'].rolling(window=sma_period).mean()
    ema_fast = combined['Attack_Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = combined['Attack_Close'].ewm(span=slow_period, adjust=False).mean()
    combined['MACD'] = ema_fast - ema_slow
    combined['Signal'] = combined['MACD'].ewm(span=signal_period, adjust=False).mean()
    combined['Histogram'] = combined['MACD'] - combined['Signal']

    trend_ok = (combined['Attack_Close'] > combined['SMA']).where(combined['SMA'].notna(), False)
    macd_ok = combined['MACD'] > combined['Signal']

    if signal_mode == "sma_exit":
        raw_values = []
        in_position = False
        for trend_value, macd_value in zip(trend_ok.values, macd_ok.values):
            if not in_position and trend_value and macd_value:
                in_position = True
            elif in_position and not trend_value:
                in_position = False
            raw_values.append(in_position)
        raw_risk_on = pd.Series(raw_values, index=combined.index)
    else:
        raw_risk_on = trend_ok & macd_ok

    if rebalance_frequency == "M":
        rebalance_dates = combined.groupby(combined.index.to_period('M')).tail(1).index
        combined['Target_Position'] = pd.Series(index=combined.index, dtype=object)
        combined.loc[rebalance_dates, 'Target_Position'] = np.where(raw_risk_on.loc[rebalance_dates], "ATTACK", "DEFENSE")
        combined['Position'] = combined['Target_Position'].shift(1).ffill().fillna("CASH")
    else:
        combined['Position'] = np.where(raw_risk_on.shift(1, fill_value=False), "ATTACK", "DEFENSE")

    if defense_df is None or defensive_mode == "현금":
        combined.loc[combined['Position'] == "DEFENSE", 'Position'] = "CASH"

    attack_div_yield = combined['Attack_Dividend'] / combined['Attack_Close'].shift(1).fillna(combined['Attack_Close'])
    defense_div_yield = combined['Defense_Dividend'] / combined['Defense_Close'].shift(1).fillna(combined['Defense_Close'])

    combined['Attack_Return'] = (
        combined['Attack_Close'] / combined['Attack_Close'].shift(1).fillna(combined['Attack_Close'])
    ) + attack_div_yield
    combined['Defense_Return'] = (
        combined['Defense_Close'] / combined['Defense_Close'].shift(1).fillna(combined['Defense_Close'])
    ).fillna(1.0) + defense_div_yield.fillna(0.0)
    combined['Cash_Return'] = 1.0

    combined['Gross_Strategy_Return'] = np.select(
        [
            combined['Position'] == "ATTACK",
            combined['Position'] == "DEFENSE",
        ],
        [
            combined['Attack_Return'],
            combined['Defense_Return'],
        ],
        default=combined['Cash_Return'],
    )

    prev_position = combined['Position'].shift(1).fillna("CASH")
    changed = combined['Position'] != prev_position
    conds = [
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
    combined['Trade_Cost'] = np.select(conds, outputs, default=2 * cost_rate)
    combined['Strategy_Return'] = (combined['Gross_Strategy_Return'] - combined['Trade_Cost']).clip(lower=0)

    hold_returns = combined['Attack_Return'].fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    combined['Hold_Return'] = hold_returns

    combined['Strategy_Cum_Return'] = (combined['Strategy_Return'].cumprod() - 1) * 100
    combined['Hold_Cum_Return'] = (combined['Hold_Return'].cumprod() - 1) * 100
    combined['Strategy_Balance'] = initial_budget * combined['Strategy_Return'].cumprod()
    combined['Hold_Balance'] = initial_budget * combined['Hold_Return'].cumprod()
    combined['Daily_Return_Pct'] = (combined['Strategy_Return'] - 1) * 100
    combined['Buy_Signal'] = combined['Position'] == "ATTACK"
    combined['Selected_Asset'] = combined['Position'].map({
        "ATTACK": attack_label,
        "DEFENSE": defense_label,
        "CASH": "현금",
    })
    return combined

def calculate_sma_macd_monthly_stats(strategy_df):
    """200일선 + MACD 전략의 월별 선택 자산과 수익률을 요약합니다."""
    stats_df = strategy_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    summary = stats_df.groupby('YearMonth').agg({
        'Selected_Asset': 'last',
        'Buy_Signal': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod',
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '월말 선택 자산', '공격자산 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

def calculate_performance_summary(backtest_df, initial_budget=10000000):
    """전략과 단순 보유의 CAGR, MDD, 변동성, 승률, 거래 횟수를 계산합니다."""
    if backtest_df.empty:
        return pd.DataFrame()

    days = max((backtest_df.index[-1] - backtest_df.index[0]).days, 1)
    years = days / 365.25

    def max_drawdown(balance):
        running_max = balance.cummax()
        drawdown = balance / running_max - 1
        return drawdown.min() * 100

    strategy_balance = backtest_df['Strategy_Balance']
    hold_balance = backtest_df['Hold_Balance']
    strategy_daily = backtest_df['Strategy_Return']
    hold_daily = backtest_df['Hold_Return']
    position = backtest_df['Selected_Asset'] if 'Selected_Asset' in backtest_df.columns else backtest_df['Buy_Signal']
    trade_count = int((position != position.shift(1)).sum() - 1)
    trade_count = max(trade_count, 0)

    rows = [
        {
            '구분': '전략',
            '최종 잔고': strategy_balance.iloc[-1],
            '누적 수익률 (%)': (strategy_balance.iloc[-1] / initial_budget - 1) * 100,
            'CAGR (%)': ((strategy_balance.iloc[-1] / initial_budget) ** (1 / years) - 1) * 100,
            'MDD (%)': max_drawdown(strategy_balance),
            '연환산 변동성 (%)': strategy_daily.sub(1).std() * np.sqrt(252) * 100,
            '일간 승률 (%)': (strategy_daily > 1).mean() * 100,
            '거래 횟수': trade_count,
        },
        {
            '구분': '단순 보유',
            '최종 잔고': hold_balance.iloc[-1],
            '누적 수익률 (%)': (hold_balance.iloc[-1] / initial_budget - 1) * 100,
            'CAGR (%)': ((hold_balance.iloc[-1] / initial_budget) ** (1 / years) - 1) * 100,
            'MDD (%)': max_drawdown(hold_balance),
            '연환산 변동성 (%)': hold_daily.sub(1).std() * np.sqrt(252) * 100,
            '일간 승률 (%)': (hold_daily > 1).mean() * 100,
            '거래 횟수': 1,
        },
    ]
    return pd.DataFrame(rows)


def calculate_sharpe_ratio(returns_series):
    """일간 수익률 시리즈를 기반으로 연율화된 샤프 지수(Sharpe Ratio)를 계산합니다.
    returns_series는 각 일자별 전략 수익률 비율(예: 1.01이면 +1% 수익)을 나타냅니다.
    """
    if returns_series is None or len(returns_series) == 0:
        return 0.0
    daily_excess_returns = returns_series - 1.0
    mean_excess = daily_excess_returns.mean()
    std_excess = daily_excess_returns.std()
    
    # 분모가 0이 되는 경우 방지
    if std_excess > 1e-9:
        return float((mean_excess / std_excess) * np.sqrt(252))
    return 0.0


def extract_trades_to_df(df, strategy_choice, initial_budget, fee_rate_pct, slippage_rate_pct):
    """각 백테스트 결과 데이터프레임을 분석하여 매수/매도 거래 이력 또는 DCA 적립 이력을 추출합니다."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    if strategy_choice == "적립식 존버 물타기 (DCA) 전략":
        purchases = []
        if 'Buy_Signal' in df.columns:
            shares = 0.0
            total_invested = 0.0
            for i, (idx, row) in enumerate(df.iterrows()):
                is_buy = row['Buy_Signal']
                price = row['종가']
                if i == 0:
                    # 최초 거치식 매수
                    injected = initial_budget
                    shares_bought = injected / (price * (1.0 + cost_rate))
                    shares += shares_bought
                    total_invested += injected
                    avg_price = price
                    purchases.append({
                        '적립일(매수일)': idx.strftime('%Y-%m-%d'),
                        '매수가격(종가)': f"{price:,.0f}원",
                        '추가 적립액': f"{injected:,.0f}원",
                        '매수 수량': f"{shares_bought:,.2f}주",
                        '누적 보유 수량': f"{shares:,.2f}주",
                        '평균 단가': f"{avg_price:,.0f}원"
                    })
                elif is_buy:
                    injected = row['Cash_Injected']
                    shares_bought = injected / (price * (1.0 + cost_rate))
                    shares += shares_bought
                    total_invested += injected
                    avg_price = total_invested / shares if shares > 0 else price
                    purchases.append({
                        '적립일(매수일)': idx.strftime('%Y-%m-%d'),
                        '매수가격(종가)': f"{price:,.0f}원",
                        '추가 적립액': f"{injected:,.0f}원",
                        '매수 수량': f"{shares_bought:,.2f}주",
                        '누적 보유 수량': f"{shares:,.2f}주",
                        '평균 단가': f"{avg_price:,.0f}원"
                    })
        return pd.DataFrame(purchases)
        
    elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
        trades = []
        if 'Buy_Signal' in df.columns and 'Buy_Price' in df.columns:
            for idx, row in df[df['Buy_Signal']].iterrows():
                buy_date = idx.strftime('%Y-%m-%d')
                buy_price = row['Buy_Price']
                sell_date = idx.strftime('%Y-%m-%d')
                sell_price = row['종가']
                ret_rate = (sell_price / buy_price - 1 - 2 * cost_rate) * 100
                
                idx_num = df.index.get_loc(idx)
                if idx_num > 0:
                    prev_balance = df['Strategy_Balance'].iloc[idx_num - 1]
                else:
                    prev_balance = initial_budget
                profit = df['Strategy_Balance'].iloc[idx_num] - prev_balance
                
                trades.append({
                    '매수일': buy_date,
                    '매수가격': f"{buy_price:,.0f}원",
                    '매도일': sell_date,
                    '매도가격': f"{sell_price:,.0f}원",
                    '수익액': f"{profit:+,.0f}원",
                    '수익률': f"{ret_rate:+.2f}%"
                })
        return pd.DataFrame(trades)
        
    # 일반 매매 전략 (추세 추종 및 보조 지표 등)
    pos_series = None
    if 'Position' in df.columns:
        pos_series = df['Position']
    elif 'Buy_Signal' in df.columns:
        pos_series = df['Buy_Signal']
    else:
        return pd.DataFrame()
        
    in_pos = pos_series.map(lambda x: True if x in [True, "ATTACK", 1, 1.0] else False)
    
    trades = []
    in_trade = False
    buy_date = None
    buy_price = 0.0
    buy_idx_loc = -1
    
    for i in range(len(df)):
        pos = in_pos.iloc[i]
        date = df.index[i]
        price = df['종가'].iloc[i]
        
        # 진입 (매수)
        if pos and not in_trade:
            in_trade = True
            buy_date = date
            buy_price = price
            buy_idx_loc = i
        # 청산 (매도)
        elif not pos and in_trade:
            in_trade = False
            sell_date = date
            sell_price = price
            
            ret_rate = (sell_price / buy_price - 1 - 2 * cost_rate) * 100
            if buy_idx_loc > 0:
                prev_balance = df['Strategy_Balance'].iloc[buy_idx_loc - 1]
            else:
                prev_balance = initial_budget
            profit = df['Strategy_Balance'].iloc[i] - prev_balance
            
            trades.append({
                '매수일': buy_date.strftime('%Y-%m-%d'),
                '매수가격': f"{buy_price:,.0f}원",
                '매도일': sell_date.strftime('%Y-%m-%d'),
                '매도가격': f"{sell_price:,.0f}원",
                '수익액': f"{profit:+,.0f}원",
                '수익률': f"{ret_rate:+.2f}%"
            })
            
    # 백테스트 종료일까지 포지션을 보유 중인 경우
    if in_trade:
        sell_date = df.index[-1]
        sell_price = df['종가'].iloc[-1]
        ret_rate = (sell_price / buy_price - 1 - cost_rate) * 100
        if buy_idx_loc > 0:
            prev_balance = df['Strategy_Balance'].iloc[buy_idx_loc - 1]
        else:
            prev_balance = initial_budget
        profit = df['Strategy_Balance'].iloc[-1] - prev_balance
        
        trades.append({
            '매수일': buy_date.strftime('%Y-%m-%d'),
            '매수가격': f"{buy_price:,.0f}원",
            '매도일': sell_date.strftime('%Y-%m-%d') + " (보유중)",
            '매도가격': f"{sell_price:,.0f}원",
            '수익액': f"{profit:+,.0f}원",
            '수익률': f"{ret_rate:+.2f}%"
        })
        
    return pd.DataFrame(trades)


def run_dca_backtest(df, initial_budget, monthly_contribution, fee_rate_pct, slippage_rate_pct, frequency="매월 첫 거래일", use_drip=False):
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    dca_df = df.copy()
    
    prices = dca_df['종가'].values
    dates = dca_df.index
    dividends = dca_df['배당금'].values if '배당금' in dca_df.columns else np.zeros(len(dca_df))
    
    portfolio_values = []
    total_invested_series = []
    cash_injections = []
    
    cash = initial_budget
    shares = 0.0
    total_invested = initial_budget
    
    if len(prices) > 0:
        shares = cash / (prices[0] * (1.0 + cost_rate))
        cash = 0.0
        
    portfolio_values.append(shares * prices[0] + cash)
    total_invested_series.append(total_invested)
    cash_injections.append(initial_budget)
    
    is_addition_day = [False] * len(dca_df)
    for i in range(1, len(dca_df)):
        current_date = dates[i]
        prev_date = dates[i-1]
        
        if frequency == "매주 첫 거래일":
            if current_date.isocalendar()[1] != prev_date.isocalendar()[1]:
                is_addition_day[i] = True
        else:
            if current_date.month != prev_date.month:
                is_addition_day[i] = True
                
    for i in range(1, len(dca_df)):
        price = prices[i]
        div = dividends[i] if use_drip else 0.0
        
        if div > 0.0 and shares > 0.0:
            div_income = shares * div
            shares_bought = div_income / (price * (1.0 + cost_rate))
            shares += shares_bought
            
        injected = 0.0
        if is_addition_day[i]:
            injected = monthly_contribution
            cash += injected
            total_invested += injected
            
            shares_bought = cash / (price * (1.0 + cost_rate))
            shares += shares_bought
            cash = 0.0
            
        portfolio_value = shares * price + cash
        portfolio_values.append(portfolio_value)
        total_invested_series.append(total_invested)
        cash_injections.append(injected)
        
    dca_df['Strategy_Balance'] = portfolio_values
    dca_df['Total_Invested'] = total_invested_series
    dca_df['Cash_Injected'] = cash_injections
    
    daily_returns = [1.0]
    for i in range(1, len(dca_df)):
        prev_val = portfolio_values[i-1]
        curr_val = portfolio_values[i]
        injected = cash_injections[i]
        ret = (curr_val - injected) / prev_val if prev_val > 0 else 1.0
        daily_returns.append(ret)
        
    dca_df['Strategy_Return'] = daily_returns
    dca_df['Strategy_Cum_Return'] = (dca_df['Strategy_Balance'] - dca_df['Total_Invested']) / dca_df['Total_Invested'] * 100
    
    daily_price_return = dca_df['종가'] / dca_df['종가'].shift(1).fillna(dca_df['종가'])
    div_yield = dca_df['배당금'] / dca_df['종가'].shift(1).fillna(dca_df['종가']) if '배당금' in dca_df.columns else 0.0
    hold_returns = (daily_price_return + div_yield).fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    dca_df['Hold_Return'] = hold_returns
    dca_df['Hold_Cum_Return'] = (dca_df['Hold_Return'].cumprod() - 1) * 100
    dca_df['Hold_Balance'] = initial_budget * dca_df['Hold_Return'].cumprod()
    
    dca_df['Daily_Return_Pct'] = (dca_df['Strategy_Return'] - 1) * 100
    dca_df['Buy_Signal'] = is_addition_day
    dca_df['Buy_Signal'].iloc[0] = True
    
    return dca_df

def calculate_dca_monthly_stats(df):
    stats_df = df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Cash_Injected': 'sum',
        'Total_Invested': 'last',
        'Strategy_Balance': 'last',
        'Hold_Balance': 'last',
    }).reset_index()
    
    summary['전략 수익률 (%)'] = (summary['Strategy_Balance'] - summary['Total_Invested']) / summary['Total_Invested'] * 100
    summary['단순 보유 수익률 (%)'] = (summary['Hold_Balance'] - df['Hold_Balance'].iloc[0]) / df['Hold_Balance'].iloc[0] * 100
    
    summary.columns = ['년-월', '적립 횟수 (회)', '월간 추가 적립액 (원)', '누적 투자 원금 (원)', '전략 평가 잔고 (원)', '단순 보유 잔고 (원)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary[['년-월', '적립 횟수 (회)', '월간 추가 적립액 (원)', '누적 투자 원금 (원)', '전략 수익률 (%)', '단순 보유 수익률 (%)']]


def calculate_max_consecutive_losses(returns_series):
    """일간 수익률 시리즈를 기반으로 최대 연속 손실 일수를 계산합니다.
    returns_series는 각 일자별 전략 수익률 비율(예: 1.01이면 +1% 수익)을 나타냅니다.
    """
    if returns_series is None or len(returns_series) == 0:
        return 0
    is_loss = returns_series < 1.0
    consecutive = is_loss.groupby((~is_loss).cumsum()).cumsum()
    return int(consecutive.max())


def run_custom_static_allocation_backtest(
    asset_data,
    target_weights,
    initial_budget,
    fee_rate_pct,
    slippage_rate_pct,
    rebalance_frequency="M",
):
    # [LOG: 20260607_2350] 사용자 정의 정적 자산배분 백테스트 엔진 구현
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    # 1. 가격 데이터 결합
    prices = pd.DataFrame({
        ticker: df["종가"]
        for ticker, df in asset_data.items()
    }).sort_index().ffill().dropna()
    
    if prices.empty:
        return pd.DataFrame()
        
    tickers = list(target_weights.keys())
    
    # 리밸런싱 시그널 생성
    if rebalance_frequency == "M":
        rebalance_dates = prices.groupby(prices.index.to_period("M")).tail(1).index
    elif rebalance_frequency == "Q":
        rebalance_dates = prices.groupby(prices.index.to_period("Q")).tail(1).index
    elif rebalance_frequency == "Y":
        rebalance_dates = prices.groupby(prices.index.to_period("Y")).tail(1).index
    else:
        rebalance_dates = pd.Index([])
        
    # 결과 데이터프레임 초기화
    out = pd.DataFrame(index=prices.index)
    
    # 일별 기록용 컬럼들
    strategy_balances = []
    strategy_returns = []
    rebalance_signals = []
    trade_costs = []
    
    # 각 자산별 가치, 비중, 수량 기록용 딕셔너리
    asset_values_hist = {t: [] for t in tickers}
    asset_weights_hist = {t: [] for t in tickers}
    asset_shares_hist = {t: [] for t in tickers}
    
    # 초기 상태 설정
    shares = {t: 0.0 for t in tickers}
    cash = initial_budget
    
    # 첫 날 거래
    first_date = prices.index[0]
    first_prices = prices.loc[first_date]
    
    # 초기 매수 실행
    total_cost_first = 0.0
    for t in tickers:
        target_val = initial_budget * target_weights[t]
        cost = target_val * cost_rate
        total_cost_first += cost
        actual_buy_amount = target_val - cost
        shares[t] = actual_buy_amount / first_prices[t]
        
    cash = 0.0
    
    # 루프 돌며 하루하루 계산
    prev_portfolio_value = initial_budget
    
    for idx, date in enumerate(prices.index):
        curr_prices = prices.loc[date]
        
        # 1. 일별 자산 가치 평가
        asset_values = {t: shares[t] * curr_prices[t] for t in tickers}
        sum_asset_values = sum(asset_values.values())
        curr_portfolio_value = sum_asset_values + cash
        
        # 2. 리밸런싱 실행 여부 판단
        is_rebalance_day = (date in rebalance_dates) and (idx > 0)
        
        trade_cost = 0.0
        if is_rebalance_day:
            # 리밸런싱 날에는 현재 총 자산을 기준으로 목표 비중만큼 재분배
            target_values = {t: curr_portfolio_value * target_weights[t] for t in tickers}
            for t in tickers:
                trade_val = target_values[t] - asset_values[t]
                trade_cost += abs(trade_val) * cost_rate
                
            curr_portfolio_value_after_cost = curr_portfolio_value - trade_cost
            for t in tickers:
                final_target_val = curr_portfolio_value_after_cost * target_weights[t]
                shares[t] = final_target_val / curr_prices[t]
                asset_values[t] = final_target_val
            
            cash = 0.0
            sum_asset_values = curr_portfolio_value_after_cost
            curr_portfolio_value = curr_portfolio_value_after_cost
            
        # 3. 일별 수익률 계산
        if idx == 0:
            daily_return = curr_portfolio_value / initial_budget
        else:
            daily_return = curr_portfolio_value / prev_portfolio_value
            
        strategy_returns.append(daily_return)
        strategy_balances.append(curr_portfolio_value)
        rebalance_signals.append(is_rebalance_day)
        trade_costs.append(trade_cost if idx > 0 else total_cost_first)
        
        # 자산별 상태 기록
        for t in tickers:
            asset_values_hist[t].append(asset_values[t])
            asset_weights_hist[t].append(asset_values[t] / curr_portfolio_value if curr_portfolio_value > 0 else 0.0)
            asset_shares_hist[t].append(shares[t])
            
        prev_portfolio_value = curr_portfolio_value
        
    # 결과 df에 값 매핑
    out['Strategy_Return'] = strategy_returns
    out['Strategy_Cum_Return'] = (pd.Series(strategy_balances, index=out.index) / initial_budget - 1.0) * 100
    out['Strategy_Balance'] = strategy_balances
    out['Rebalance_Signal'] = rebalance_signals
    out['Trade_Cost'] = trade_costs
    out['Daily_Return_Pct'] = (out['Strategy_Return'] - 1.0) * 100
    
    # 단순 보유 (첫 번째 입력된 자산 기준)
    benchmark_ticker = tickers[0]
    bench_prices = prices[benchmark_ticker]
    out['Hold_Return'] = bench_prices / bench_prices.shift(1).fillna(bench_prices)
    hold_returns_array = out['Hold_Return'].values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    out['Hold_Return'] = hold_returns_array
    out['Hold_Cum_Return'] = (out['Hold_Return'].cumprod() - 1.0) * 100
    out['Hold_Balance'] = initial_budget * out['Hold_Return'].cumprod()
    
    out['Selected_Asset'] = benchmark_ticker
    
    # 자산별 데이터 컬럼 추가
    for t in tickers:
        out[f"{t}_Value"] = asset_values_hist[t]
        out[f"{t}_Weight"] = asset_weights_hist[t]
        out[f"{t}_Shares"] = asset_shares_hist[t]
        
    return out


def calculate_custom_static_allocation_monthly_stats(result_df, tickers):
    # [LOG: 20260607_2350] 사용자 정의 정적 자산배분 월별 통계 함수 구현
    stats_df = result_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    
    # 월별 리밸런싱 횟수
    stats_df['Rebalance_Count'] = np.where(stats_df['Rebalance_Signal'], 1, 0)
    
    # 월말 자산별 비중 계산용 agg 딕셔너리
    agg_dict = {
        'Rebalance_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }
    for t in tickers:
        agg_dict[f"{t}_Weight"] = 'last'
        
    summary = stats_df.groupby('YearMonth').agg(agg_dict).reset_index()
    
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1.0) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1.0) * 100
    
    rename_cols = {
        'YearMonth': '년-월',
        'Rebalance_Count': '리밸런싱 횟수 (회)',
        'Strategy_Return': '전략 수익률 (%)',
        'Hold_Return': '단순 보유 수익률 (%)'
    }
    for t in tickers:
        rename_cols[f"{t}_Weight"] = f"월말 {t} 비중 (%)"
        summary[f"{t}_Weight"] = summary[f"{t}_Weight"] * 100
        
    summary = summary.rename(columns=rename_cols)
    return summary
