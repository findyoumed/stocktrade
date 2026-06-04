import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "chapter3"))

from data_loader import load_data

df = load_data("20240101", "20251231", "161510")
print("Data columns:", df.columns)
print("Data shape:", df.shape)
if '배당금' in df.columns:
    print("Total dividends in df:", df['배당금'].sum())
    print("Non-zero dividends in df:")
    print(df[df['배당금'] > 0]['배당금'])
else:
    print("배당금 column not found in df!")
