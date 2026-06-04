import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "chapter3"))

from data_loader import load_data
from backtest_engine import prepare_features, run_rolling_forecast, run_ml_backtest

df = load_data("20240101", "20251231", "161510")
X, y = prepare_features(df)
pred_series = run_rolling_forecast(X, y, 90)

# Backtest with use_drip=False
ml_df_nodrip = run_ml_backtest(df, pred_series, 10000000, 0.15, 0.10, use_drip=False)
nodrip_strategy_return = ml_df_nodrip['Strategy_Cum_Return'].iloc[-1]
nodrip_hold_return = ml_df_nodrip['Hold_Cum_Return'].iloc[-1]

# Backtest with use_drip=True
ml_df_drip = run_ml_backtest(df, pred_series, 10000000, 0.15, 0.10, use_drip=True)
drip_strategy_return = ml_df_drip['Strategy_Cum_Return'].iloc[-1]
drip_hold_return = ml_df_drip['Hold_Cum_Return'].iloc[-1]

print(f"No DRIP strategy return: {nodrip_strategy_return:.4f}%")
print(f"No DRIP hold return: {nodrip_hold_return:.4f}%")
print(f"DRIP strategy return: {drip_strategy_return:.4f}%")
print(f"DRIP hold return: {drip_hold_return:.4f}%")
