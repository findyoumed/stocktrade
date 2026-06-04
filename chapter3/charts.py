# [LOG: 20260604_1952]
import pandas as pd
import plotly.graph_objects as go

def add_dividend_markers_to_fig(fig, df):
    """
    차트에 배당금 지급 마커를 추가합니다. (plus_dividend 프로젝트에서 착안)
    """
    if df is not None and '배당금' in df.columns:
        div_days = df[df['배당금'] > 0]
        if not div_days.empty:
            # 배당금이 지급된 지점에 삼각형 마커 표시 및 텍스트 금액 오버레이
            fig.add_trace(go.Scatter(
                x=div_days.index,
                y=div_days['종가'],
                mode='markers+text',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#22c55e', # Green
                    line=dict(width=1, color='black')
                ),
                text=[f"₩{int(amt)}" for amt in div_days['배당금']],
                textposition="top center",
                name="배당금 지급일",
                hovertemplate='<b>배당금 지급일</b><br>날짜: %{x}<br>주가: %{y:,.0f}원<br>배당금: %{text}<extra></extra>'
            ))
