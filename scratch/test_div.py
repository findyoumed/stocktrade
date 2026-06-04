import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "chapter3"))

from data_loader import get_dividends_df

# Mock trading dates
trading_dates = {"2024-04-30", "2024-05-31", "2024-06-28", "2024-12-30", "2025-04-30"}
res = get_dividends_df("161510", "20240101", "20251231", trading_dates)
print("Dividends for 161510:")
print(res[res > 0])
