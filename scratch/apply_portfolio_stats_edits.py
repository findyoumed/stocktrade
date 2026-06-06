import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

target_def = """def calculate_signal_monthly_stats(strategy_df):
    stats_df = strategy_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod',
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary"""

replacement_def = """def calculate_signal_monthly_stats(strategy_df, is_portfolio=False):
    stats_df = strategy_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    stats_df['Working_Days'] = 1
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Working_Days': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod',
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    if is_portfolio:
        summary.columns = ['년-월', '리밸런싱 횟수 (회)', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
        summary = summary[['년-월', '매수 보유 일수 (일)', '리밸런싱 횟수 (회)', '전략 수익률 (%)', '단순 보유 수익률 (%)']]
    else:
        summary = summary.drop(columns=['Working_Days'])
        summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary"""

if target_def in content:
    content = content.replace(target_def, replacement_def)
    print("Replaced calculate_signal_monthly_stats definition successfully.")
else:
    # Try normalizing line endings
    content_lf = content.replace("\\r\\n", "\\n")
    target_lf = target_def.replace("\\r\\n", "\\n")
    replacement_lf = replacement_def.replace("\\r\\n", "\\n")
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf)
        print("Replaced calculate_signal_monthly_stats with LF normalization.")
    else:
        print("Could not find targets.")

# Now replace the invocation of calculate_signal_monthly_stats in the main rendering block
target_call = """                else:
                    summary_stats = calculate_signal_monthly_stats(generic_df)
                    target_df = generic_df"""

replacement_call = """                else:
                    is_portfolio = strategy_choice in ["영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]
                    summary_stats = calculate_signal_monthly_stats(generic_df, is_portfolio=is_portfolio)
                    target_df = generic_df"""

if target_call in content:
    content = content.replace(target_call, replacement_call)
    print("Replaced call successfully.")
else:
    content_lf = content.replace("\\r\\n", "\\n")
    target_lf = target_call.replace("\\r\\n", "\\n")
    replacement_lf = replacement_call.replace("\\r\\n", "\\n")
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf)
        print("Replaced call with LF normalization.")
    else:
        print("Could not find call targets.")

dashboard_path.write_text(content, encoding="utf-8")
