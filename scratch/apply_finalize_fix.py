import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

target = """        elif prev_position and not position:
            # 주식 -> 현금 (매도 청산): 당일 종가에 청산하고 현금화, 주가 변화량 반영 및 매도 수수료 차감
            ret = daily_price_return.iloc[i] - cost_rate + d_yield"""

replacement = """        elif prev_position and not position:
            # 주식 -> 현금 (매도 청산): 당일은 현금 보유 상태이므로 주가 변동을 반영하지 않고 수수료만 차감
            ret = 1.0 - cost_rate"""

if target in content:
    content = content.replace(target, replacement)
    dashboard_path.write_text(content, encoding="utf-8")
    print("Successfully corrected cash-return on sell days in finalize_signal_backtest.")
else:
    # Try with LF normalization
    content_lf = content.replace("\r\n", "\n")
    target_lf = target.replace("\r\n", "\n")
    replacement_lf = replacement.replace("\r\n", "\n")
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf)
        dashboard_path.write_text(content, encoding="utf-8")
        print("Successfully corrected cash-return on sell days with LF normalization.")
    else:
        print("Target content not found.")
