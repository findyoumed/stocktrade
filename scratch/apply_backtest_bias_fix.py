import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
engine_path = Path("chapter3/backtest_engine.py")

# 1. Fix stock_prediction_dashboard.py
content_dash = dashboard_path.read_text(encoding="utf-8")

# Fix run_ma_cross_backtest
target_ma = """    ma_df['Buy_Signal'] = ma_df['SMA_Short'] > ma_df['SMA_Long']
    ma_df['Buy_Signal'] = np.where(pd.isna(ma_df['SMA_Long']), False, ma_df['Buy_Signal'])"""

replacement_ma = """    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    raw_signal = ma_df['SMA_Short'] > ma_df['SMA_Long']
    raw_signal = np.where(pd.isna(ma_df['SMA_Long']), False, raw_signal)
    ma_df['Buy_Signal'] = pd.Series(raw_signal, index=ma_df.index).shift(1).fillna(False)"""

# Fix run_rsi_backtest
target_rsi = """    rsi_df['Buy_Signal'] = signals"""
replacement_rsi = """    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    rsi_df['Buy_Signal'] = pd.Series(signals, index=rsi_df.index).shift(1).fillna(False)"""

# Fix run_bollinger_backtest
target_bb = """    bb_df['Buy_Signal'] = signals"""
replacement_bb = """    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    bb_df['Buy_Signal'] = pd.Series(signals, index=bb_df.index).shift(1).fillna(False)"""

# Fix finalize_signal_backtest
target_finalize = """    out['Buy_Signal'] = out['Buy_Signal'].fillna(False).astype(bool)"""
replacement_finalize = """    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    out['Buy_Signal'] = out['Buy_Signal'].fillna(False).astype(bool).shift(1).fillna(False)"""


# Perform replacements on dashboard
if target_ma in content_dash:
    content_dash = content_dash.replace(target_ma, replacement_ma)
    print("Replaced run_ma_cross_backtest in dashboard.")
else:
    print("Could not find target_ma in dashboard.")

if target_rsi in content_dash:
    content_dash = content_dash.replace(target_rsi, replacement_rsi)
    print("Replaced run_rsi_backtest in dashboard.")
else:
    print("Could not find target_rsi in dashboard.")

if target_bb in content_dash:
    content_dash = content_dash.replace(target_bb, replacement_bb)
    print("Replaced run_bollinger_backtest in dashboard.")
else:
    print("Could not find target_bb in dashboard.")

if target_finalize in content_dash:
    content_dash = content_dash.replace(target_finalize, replacement_finalize)
    print("Replaced finalize_signal_backtest in dashboard.")
else:
    print("Could not find target_finalize in dashboard.")

dashboard_path.write_text(content_dash, encoding="utf-8")


# 2. Fix backtest_engine.py
content_eng = engine_path.read_text(encoding="utf-8")

# Fix run_macd_backtest
target_macd = """    # 매수 조건: MACD선이 Signal선 위에 있을 때 보유 유지
    macd_df['Buy_Signal'] = macd_df['MACD'] > macd_df['Signal']
    macd_df['Buy_Signal'] = np.where(pd.isna(macd_df['Signal']), False, macd_df['Buy_Signal'])"""

replacement_macd = """    # 매수 조건: MACD선이 Signal선 위에 있을 때 보유 유지
    raw_signal = macd_df['MACD'] > macd_df['Signal']
    raw_signal = np.where(pd.isna(macd_df['Signal']), False, raw_signal)
    # [LOG: 20260607_0106] 미래 참조 편향 방지를 위해 시그널을 1영업일 shift
    macd_df['Buy_Signal'] = pd.Series(raw_signal, index=macd_df.index).shift(1).fillna(False)"""

if target_macd in content_eng:
    content_eng = content_eng.replace(target_macd, replacement_macd)
    print("Replaced run_macd_backtest in engine.")
else:
    print("Could not find target_macd in engine.")

engine_path.write_text(content_eng, encoding="utf-8")
print("Done.")
