import sys
from pathlib import Path

dashboard_path = Path("chapter3/stock_prediction_dashboard.py")
content = dashboard_path.read_text(encoding="utf-8")

# 1. Modify ML strategy monthly table sorting (descending order of year-month)
target_ml = """                with col_table:
                    st.write("📊 **월별 통계 요약 데이터**")
                    display_df = monthly_stats.copy()"""
replacement_ml = """                with col_table:
                    st.write("📊 **월별 통계 요약 데이터**")
                    display_df = monthly_stats.copy().sort_values(by="년-월", ascending=False)"""

content = content.replace(target_ml, replacement_ml)

# 2. Modify other strategies monthly table sorting (descending order of year-month)
target_other = """                with col_table:
                    st.write("📅 **월별 거래 요약 데이터**")
                    display_stats = summary_stats.copy()"""
replacement_other = """                with col_table:
                    st.write("📅 **월별 거래 요약 데이터**")
                    display_stats = summary_stats.copy().sort_values(by="년-월", ascending=False)"""

content = content.replace(target_other, replacement_other)

# 3. Modify combined strategy monthly table sorting (descending order of year-month)
target_combined = """                with col_table:
                    st.write("📊 **월별 전략별 수익률 대조 테이블**")
                    display_stats = combined_stats.copy()"""
replacement_combined = """                with col_table:
                    st.write("📊 **월별 전략별 수익률 대조 테이블**")
                    display_stats = combined_stats.copy().sort_values(by="년-월", ascending=False)"""

content = content.replace(target_combined, replacement_combined)

dashboard_path.write_text(content, encoding="utf-8")
print("Replaced all monthly summary table sorting logic to descending (newest on top).")
