import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# 1. Protect Stochastic Oscillator from division by zero
target_stoch = "stoch_df['%K'] = ((stoch_df['종가'] - low_min) / (high_max - low_min)) * 100"
replacement_stoch = "stoch_df['%K'] = ((stoch_df['종가'] - low_min) / (high_max - low_min).replace(0, 1e-10)) * 100"

# 2. Protect ADX / DMI from division by zero
target_adx_1 = "adx_df['+DI'] = 100 * plus_dm.rolling(period).mean() / atr"
replacement_adx_1 = "adx_df['+DI'] = 100 * plus_dm.rolling(period).mean() / atr.replace(0, 1e-10)"

target_adx_2 = "adx_df['-DI'] = 100 * minus_dm.rolling(period).mean() / atr"
replacement_adx_2 = "adx_df['-DI'] = 100 * minus_dm.rolling(period).mean() / atr.replace(0, 1e-10)"

target_adx_3 = "dx = ((adx_df['+DI'] - adx_df['-DI']).abs() / (adx_df['+DI'] + adx_df['-DI'])) * 100"
replacement_adx_3 = "dx = ((adx_df['+DI'] - adx_df['-DI']).abs() / (adx_df['+DI'] + adx_df['-DI']).replace(0, 1e-10)) * 100"

modified = False
if target_stoch in content:
    content = content.replace(target_stoch, replacement_stoch)
    print("Protected Stochastic Oscillator division.")
    modified = True

if target_adx_1 in content:
    content = content.replace(target_adx_1, replacement_adx_1)
    print("Protected ADX +DI division.")
    modified = True

if target_adx_2 in content:
    content = content.replace(target_adx_2, replacement_adx_2)
    print("Protected ADX -DI division.")
    modified = True

if target_adx_3 in content:
    content = content.replace(target_adx_3, replacement_adx_3)
    print("Protected ADX DX division.")
    modified = True

if modified:
    dashboard_path.write_text(content, encoding="utf-8")
    print("Successfully saved dashboard files.")
else:
    print("No changes were necessary or targets not found.")
