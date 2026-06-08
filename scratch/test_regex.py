import re

filepath = r"d:\work\stocktrade\chapter3\stock_prediction_dashboard.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

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
    match = re.search(pattern, content)
    if match:
        print(f"Match for {func}:")
        lines = match.group(0).strip().split("\n")
        print(f"  Starts: {lines[0]}")
        print(f"  Ends:   {lines[-1]}")
        print(f"  Lines:  {len(lines)}")
    else:
        print(f"Warning: could not match {func}")
