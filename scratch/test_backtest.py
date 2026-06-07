import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add chapter3 to path to import functions
sys.path.append(str(Path("chapter3").absolute()))

from stock_prediction_dashboard import (
    run_stochastic_backtest,
    run_ma_cross_backtest,
)
from backtest_engine import (
    run_macd_backtest,
)

# 1. Generate 100 days of mock price data (a wave pattern with some noise)
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
prices = 10000.0
price_history = []
for i in range(100):
    prices += np.sin(i / 5.0) * 200.0 + np.random.normal(0, 100)
    price_history.append(max(prices, 1000.0))

df = pd.DataFrame(index=dates)
df['종가'] = price_history
df['시가'] = df['종가'] * (1.0 + np.random.normal(0, 0.01, 100))
df['고가'] = df[['종가', '시가']].max(axis=1) * 1.02
df['저가'] = df[['종가', '시가']].min(axis=1) * 0.98
df['거래량'] = np.random.randint(10000, 100000, 100)
df['배당금'] = 0.0

initial_budget = 10_000_000
fee_rate = 0.15
slippage_rate = 0.10

# 2. Run Stochastic Backtest
stoch_df = run_stochastic_backtest(df, k_period=14, d_period=3, initial_budget=initial_budget, fee_rate_pct=fee_rate, slippage_rate_pct=slippage_rate)
print(f"=== 스토캐스틱 백테스트 결과 ===")
print(f"최종 전략 잔고: {stoch_df['Strategy_Balance'].iloc[-1]:,.0f}원")
print(f"최종 누적 수익률: {stoch_df['Strategy_Cum_Return'].iloc[-1]:.2f}%")

# 3. Run MA Cross Backtest
ma_df = run_ma_cross_backtest(df, short_period=5, long_period=20, initial_budget=initial_budget, fee_rate_pct=fee_rate, slippage_rate_pct=slippage_rate)
print(f"=== 이동평균 골든크로스 백테스트 결과 ===")
print(f"최종 전략 잔고: {ma_df['Strategy_Balance'].iloc[-1]:,.0f}원")
print(f"최종 누적 수익률: {ma_df['Strategy_Cum_Return'].iloc[-1]:.2f}%")

# 4. Run MACD Backtest
macd_df = run_macd_backtest(df, fast_period=12, slow_period=26, signal_period=9, initial_budget=initial_budget, fee_rate_pct=fee_rate, slippage_rate_pct=slippage_rate)
print(f"=== MACD 백테스트 결과 ===")
print(f"최종 전략 잔고: {macd_df['Strategy_Balance'].iloc[-1]:,.0f}원")
print(f"최종 누적 수익률: {macd_df['Strategy_Cum_Return'].iloc[-1]:.2f}%")
print(f"단순 보유 누적 수익률: {macd_df['Hold_Cum_Return'].iloc[-1]:.2f}%")
