import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# Define a robust simulation-based finalize_signal_backtest to prevent compound-rate scaling issues
target_def = """def finalize_signal_backtest(signal_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"Boolean Buy_Signal 컬럼을 가진 전략 DataFrame에 수익률/잔고 컬럼을 붙입니다.\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    out = signal_df.copy()
    out['Buy_Signal'] = out['Buy_Signal'].fillna(False).astype(bool)
    prev_signals = out['Buy_Signal'].shift(1).fillna(False)
    entry_cost = np.where(out['Buy_Signal'] & ~prev_signals, cost_rate, 0.0)
    exit_cost = np.where(~out['Buy_Signal'] & prev_signals, cost_rate, 0.0)
    total_cost = entry_cost + exit_cost

    if use_drip and '배당금' in out.columns:
        div_yield = out['배당금'] / out['종가'].shift(1).fillna(out['종가'])
        strategy_div_yield = np.where(out['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0

    daily_price_return = out['종가'] / out['종가'].shift(1).fillna(out['종가'])
    out['Strategy_Return'] = np.where(
        out['Buy_Signal'],
        daily_price_return - total_cost + strategy_div_yield,
        1.0 - total_cost,
    )
    out['Strategy_Return'] = out['Strategy_Return'].fillna(1.0)

    hold_returns = (daily_price_return + div_yield).fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    out['Hold_Return'] = hold_returns
    out['Strategy_Cum_Return'] = (out['Strategy_Return'].cumprod() - 1) * 100
    out['Hold_Cum_Return'] = (out['Hold_Return'].cumprod() - 1) * 100
    out['Strategy_Balance'] = initial_budget * out['Strategy_Return'].cumprod()
    out['Hold_Balance'] = initial_budget * out['Hold_Return'].cumprod()
    out['Daily_Return_Pct'] = (out['Strategy_Return'] - 1) * 100
    return out"""

replacement_def = """def finalize_signal_backtest(signal_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    \"\"\"Boolean Buy_Signal 컬럼을 가진 전략 DataFrame에 수익률/잔고 컬럼을 붙입니다.
    실물 매매 시뮬레이션 방식을 도입하여 현금 상태와 주식 보유 상태의 수익률 왜곡(복리 버그)을 완벽히 교정합니다.
    \"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    out = signal_df.copy()
    out['Buy_Signal'] = out['Buy_Signal'].fillna(False).astype(bool)
    
    # 1. 일별 주가 등락 및 배당수익률 계산
    daily_price_return = out['종가'] / out['종가'].shift(1).fillna(out['종가'])
    if '배당금' in out.columns:
        div_yield = out['배당금'] / out['종가'].shift(1).fillna(out['종가'])
    else:
        div_yield = 0.0
        
    # 2. 거래 시뮬레이션 수행 (포지션 상태 관리)
    strategy_returns = []
    position = False  # False: 현금, True: 주식 보유
    
    closes = out['종가'].values
    signals = out['Buy_Signal'].values
    div_yields = div_yield.values if isinstance(div_yield, pd.Series) else np.zeros(len(out))
    
    for i in range(len(out)):
        sig = signals[i]
        d_yield = div_yields[i] if use_drip else 0.0
        
        # 이전 거래일의 포지션 상태 저장
        prev_position = position
        
        # 당일 시그널에 따른 포지션 결정 (종가 기준 결정)
        position = sig
        
        # 일별 전략 수익률 산출
        if not prev_position and not position:
            # 현금 -> 현금: 수익률 변동 없음 (1.0)
            ret = 1.0
        elif not prev_position and position:
            # 현금 -> 주식 (매수 진입): 당일은 시가 매수 진입으로 가정하여 종가 변화량 반영 및 매수 수수료 차감
            ret = daily_price_return.iloc[i] - cost_rate + d_yield
        elif prev_position and not position:
            # 주식 -> 현금 (매도 청산): 당일 종가에 청산하고 현금화, 주가 변화량 반영 및 매도 수수료 차감
            ret = daily_price_return.iloc[i] - cost_rate + d_yield
        else:
            # 주식 -> 주식 (보유 유지): 주가 등락률 및 배당 재투자 반영
            ret = daily_price_return.iloc[i] + d_yield
            
        # 수수료 차감 등으로 마이너스 자산이 되는 것을 방어
        if ret < 0:
            ret = 0.0
        strategy_returns.append(ret)
        
    out['Strategy_Return'] = pd.Series(strategy_returns, index=out.index).fillna(1.0)
    
    # 3. 단순 보유 수익률 계산 (최초 1회 진입 수수료 반영)
    hold_returns = (daily_price_return + div_yield).fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    out['Hold_Return'] = hold_returns
    
    # 4. 누적 지표 계산
    out['Strategy_Cum_Return'] = (out['Strategy_Return'].cumprod() - 1) * 100
    out['Hold_Cum_Return'] = (out['Hold_Return'].cumprod() - 1) * 100
    out['Strategy_Balance'] = initial_budget * out['Strategy_Return'].cumprod()
    out['Hold_Balance'] = initial_budget * out['Hold_Return'].cumprod()
    out['Daily_Return_Pct'] = (out['Strategy_Return'] - 1) * 100
    return out"""

if target_def in content:
    content = content.replace(target_def, replacement_def)
    print("Replaced finalize_signal_backtest successfully.")
else:
    content_lf = content.replace("\r\n", "\n")
    target_lf = target_def.replace("\r\n", "\n")
    replacement_lf = replacement_def.replace("\r\n", "\n")
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf)
        print("Replaced finalize_signal_backtest with LF normalization.")
    else:
        print("Could not find targets in file.")

dashboard_path.write_text(content, encoding="utf-8")
