import numpy as np
import pandas as pd
import sys
import json
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
from backtest_engine import (
    calculate_dual_momentum_monthly_stats,
    calculate_macd_monthly_stats,
    run_dual_momentum_backtest,
    run_macd_backtest,
)

# [LOG: 20260604_1357]

UNKNOWN_TICKER_NAME = "알 수 없는 종목"
INVALID_TICKER_HINTS = {
    "396580": "ACE 미국30년국채액티브(H)의 종목코드는 453850입니다."
}
KOREAN_TICKER_ALIASES = {
    "삼성전자": "005930",
    "samsungelectronics": "005930",
    "samsungelec": "005930",
    "네이버": "035420",
    "naver": "035420",
    "카카오": "035720",
    "kakao": "035720",
    "현대차": "005380",
    "hyundai": "005380",
    "기아": "000270",
    "kia": "000270",
}
LOCAL_TICKER_CATALOG = {
    "005930": {"name": "삼성전자", "aliases": ["Samsung Electronics", "SamsungElec"]},
    "005935": {"name": "삼성전자우", "aliases": ["Samsung Electronics Preferred"]},
    "006400": {"name": "삼성SDI", "aliases": ["Samsung SDI"]},
    "006405": {"name": "삼성SDI우", "aliases": ["Samsung SDI Preferred"]},
    "207940": {"name": "삼성바이오로직스", "aliases": ["Samsung Biologics"]},
    "028260": {"name": "삼성물산", "aliases": ["Samsung C&T"]},
    "02826K": {"name": "삼성물산우B", "aliases": ["Samsung C&T Preferred"]},
    "018260": {"name": "삼성에스디에스", "aliases": ["Samsung SDS"]},
    "032830": {"name": "삼성생명", "aliases": ["Samsung Life"]},
    "000810": {"name": "삼성화재", "aliases": ["Samsung Fire & Marine"]},
    "000815": {"name": "삼성화재우", "aliases": ["Samsung Fire & Marine Preferred"]},
    "029780": {"name": "삼성카드", "aliases": ["Samsung Card"]},
    "016360": {"name": "삼성증권", "aliases": ["Samsung Securities"]},
    "010140": {"name": "삼성중공업", "aliases": ["Samsung Heavy Industries"]},
    "010145": {"name": "삼성중공우", "aliases": ["Samsung Heavy Industries Preferred"]},
    "006660": {"name": "삼성공조", "aliases": ["Samsung Climate Control"]},
    "448730": {"name": "삼성FN리츠", "aliases": ["Samsung FN REIT"]},
    "360750": {"name": "TIGER 미국S&P500", "aliases": []},
    "379800": {"name": "KODEX 미국S&P500TR", "aliases": []},
    "365000": {"name": "ACE 미국S&P500", "aliases": []},
    "314250": {"name": "KODEX 미국나스닥100TR", "aliases": []},
    "133690": {"name": "TIGER 미국나스닥100", "aliases": []},
    "252670": {"name": "KODEX 200선물인버스2X", "aliases": []},
    "114800": {"name": "KODEX 인버스", "aliases": []},
    "122630": {"name": "KODEX 레버리지", "aliases": []},
    "453850": {"name": "ACE 미국30년국채액티브(H)", "aliases": []},
    "476560": {"name": "KODEX 미국30년국채액티브(H)", "aliases": []},
    "458250": {"name": "TIGER 미국30년국채액티브(H)", "aliases": []},
    "035420": {"name": "네이버", "aliases": ["NAVER", "naver", "nav"]},
    "035720": {"name": "카카오", "aliases": ["Kakao", "kakao", "kaka"]},
    "005380": {"name": "현대차", "aliases": ["Hyundai Motor", "hyundai", "hyeon"]},
    "000270": {"name": "기아", "aliases": ["Kia", "kia"]},
    "003550": {"name": "LG", "aliases": ["LG", "lg", "엘지"]},
    "066570": {"name": "LG전자", "aliases": ["LG Electronics", "lg전자", "엘지전자"]},
    "051910": {"name": "LG화학", "aliases": ["LG Chem", "lg화학", "엘지화학"]},
    "000660": {"name": "SK하이닉스", "aliases": ["SK Hynix", "sk하이닉스", "에스케이하이닉스", "하이닉스"]},
    "034730": {"name": "SK", "aliases": ["SK", "sk", "에스케이"]},
    "017670": {"name": "SK텔레콤", "aliases": ["SK Telecom", "sk텔레콤", "에스케이텔레콤"]},
}


FINANCIALS_KR = {
    'Total Revenue': '총수익(매출액)', 
    'Cost Of Revenue': '매출원가',
    'Gross Profit': '매출총이익',
    'Research And Development': '연구개발비',
    'Selling General And Administration': '판관비',
    'Operating Income': '영업이익', 
    'EBITDA': 'EBITDA',
    'EBIT': 'EBIT',
    'Pretax Income': '법인세차감전이익',
    'Tax Provision': '법인세비용',
    'Net Income': '당기순이익',
    'Basic EPS': '기본 EPS',
    'Diluted EPS': '희석 EPS',
    'Total Assets': '총자산', 
    'Current Assets': '유동자산',
    'Cash And Cash Equivalents': '현금및현금성자산',
    'Accounts Receivable': '매출채권',
    'Inventory': '재고자산',
    'Net PPE': '유형자산',
    'Total Liabilities Net Minority Interest': '총부채', 
    'Current Liabilities': '유동부채',
    'Accounts Payable': '매입채무',
    'Total Debt': '총차입금',
    'Net Debt': '순차입금',
    'Stockholders Equity': '자본총계',
    'Operating Cash Flow': '영업활동현금흐름', 
    'Investing Cash Flow': '투자활동현금흐름',
    'Financing Cash Flow': '재무활동현금흐름',
    'Capital Expenditure': '자본적지출',
    'Free Cash Flow': '잉여현금흐름',
    'Repurchase Of Capital Stock': '자사주매입',
    'Cash Dividends Paid': '배당금지급'
}

KEY_METRICS = {
    'trailingPE': ('PER (최근 12개월)', 'ratio'),
    'forwardPE': ('PER (선행 12개월)', 'ratio'),
    'priceToBook': ('PBR (주가순자산비율)', 'ratio'),
    'returnOnEquity': ('ROE (자기자본이익률)', 'percent'),
    'returnOnAssets': ('ROA (총자산이익률)', 'percent'),
    'enterpriseToEbitda': ('EV/EBITDA', 'ratio'),
    'dividendYield': ('배당수익률', 'yield_percent'),
    'operatingMargins': ('영업이익률', 'percent'),
    'profitMargins': ('순이익률', 'percent'),
    'grossMargins': ('매출총이익률', 'percent'),
    'ebitdaMargins': ('EBITDA 마진', 'percent'),
    'revenueGrowth': ('매출 성장률', 'percent'),
    'earningsGrowth': ('순이익 성장률', 'percent'),
    'debtToEquity': ('부채비율 (Debt/Equity)', 'ratio'),
    'currentRatio': ('유동비율', 'ratio'),
    'quickRatio': ('당좌비율', 'ratio'),
    'beta': ('베타', 'ratio'),
    'marketCap': ('시가총액', 'large'),
    'enterpriseValue': ('기업가치 (EV)', 'large'),
    'totalRevenue': ('최근 매출액', 'large'),
    'ebitda': ('EBITDA', 'large'),
    'freeCashflow': ('잉여현금흐름', 'large'),
    'operatingCashflow': ('영업활동현금흐름', 'large'),
    'trailingEps': ('EPS (최근 12개월)', 'ratio'),
    'forwardEps': ('EPS (선행 12개월)', 'ratio'),
    'bookValue': ('주당순자산 (BPS)', 'ratio'),
    'payoutRatio': ('배당성향', 'percent'),
    'sharesOutstanding': ('발행주식수', 'large'),
    'floatShares': ('유통주식수', 'large'),
    'heldPercentInsiders': ('내부자 보유비중', 'percent'),
    'heldPercentInstitutions': ('기관 보유비중', 'percent'),
    'shortRatio': ('공매도 커버일수', 'ratio'),
    'shortPercentOfFloat': ('유통주식 대비 공매도', 'percent'),
    'fiftyTwoWeekLow': ('52주 최저가', 'ratio'),
    'fiftyTwoWeekHigh': ('52주 최고가', 'ratio'),
    'targetMeanPrice': ('애널리스트 평균 목표가', 'ratio'),
}

CORE_METRIC_KEYS = [
    'priceToBook',
    'returnOnEquity',
    'trailingPE',
    'forwardPE',
    'enterpriseToEbitda',
    'returnOnAssets',
    'dividendYield',
    'operatingMargins',
    'profitMargins',
]

KEY_METRICS_CACHE_VERSION = "20260606_roe_per_pbr_fallback_v2"

INDEX_ETF_CATALOG = {
    "미국 대표지수 추종": [
        {"지수": "S&P 500", "티커": "SPY", "운용사": "State Street Global Advisors", "종목명": "SPDR S&P 500 ETF Trust", "의미": "미국 대형주 대표 지수 추종"},
        {"지수": "S&P 500", "티커": "IVV", "운용사": "BlackRock iShares", "종목명": "iShares Core S&P 500 ETF", "의미": "미국 대형주 대표 지수 추종"},
        {"지수": "S&P 500", "티커": "VOO", "운용사": "Vanguard", "종목명": "Vanguard S&P 500 ETF", "의미": "미국 대형주 대표 지수 추종"},
        {"지수": "NASDAQ 100", "티커": "QQQ", "운용사": "Invesco", "종목명": "Invesco QQQ Trust", "의미": "미국 대형 기술주 중심 지수 추종"},
        {"지수": "NASDAQ 100", "티커": "QQQM", "운용사": "Invesco", "종목명": "Invesco NASDAQ 100 ETF", "의미": "미국 대형 기술주 중심 지수 추종"},
        {"지수": "Dow Jones Industrial Average", "티커": "DIA", "운용사": "State Street Global Advisors", "종목명": "SPDR Dow Jones Industrial Average ETF", "의미": "미국 대표 우량 대형주 지수 추종"},
        {"지수": "Dow Jones U.S. Index", "티커": "IYY", "운용사": "BlackRock iShares", "종목명": "iShares Dow Jones U.S. ETF", "의미": "미국 대형주와 중형주 중심의 Dow Jones U.S. Index 추종"},
        {"지수": "Russell 2000", "티커": "IWM", "운용사": "BlackRock iShares", "종목명": "iShares Russell 2000 ETF", "의미": "미국 소형주 지수 추종"},
        {"지수": "Russell 2000", "티커": "VTWO", "운용사": "Vanguard", "종목명": "Vanguard Russell 2000 ETF", "의미": "미국 소형주 지수 추종"},
        {"지수": "Russell 2000 기반", "티커": "OMFS", "운용사": "Invesco", "종목명": "Invesco Russell 2000 Dynamic Multifactor ETF", "의미": "Russell 2000 기반 미국 소형주 멀티팩터 전략 추종"},
        {"지수": "미국 광범위 시장", "티커": "VTI", "운용사": "Vanguard", "종목명": "Vanguard Total Stock Market ETF", "의미": "미국 전체 주식시장 추종"},
        {"지수": "미국 광범위 시장", "티커": "ITOT", "운용사": "BlackRock iShares", "종목명": "iShares Core S&P Total U.S. Stock Market ETF", "의미": "미국 전체 주식시장 추종"},
        {"지수": "미국 광범위 시장", "티커": "SCHB", "운용사": "Schwab", "종목명": "Schwab U.S. Broad Market ETF", "의미": "미국 전체 주식시장 추종"},
        {"지수": "S&P Composite 1500", "티커": "SPTM", "운용사": "State Street Global Advisors", "종목명": "SPDR Portfolio S&P 1500 Composite Stock Market ETF", "의미": "미국 대형주, 중형주, 소형주를 포함한 광범위한 미국 주식시장 추종"},
    ],
    "글로벌 지수 ETF": [
        {"지수": "전세계 주식", "티커": "VT", "운용사": "Vanguard", "종목명": "Vanguard Total World Stock ETF", "의미": "선진국과 신흥국을 포함한 전세계 주식시장 추종"},
        {"지수": "전세계 주식", "티커": "ACWI", "운용사": "BlackRock iShares", "종목명": "iShares MSCI ACWI ETF", "의미": "MSCI ACWI 기반 전세계 주식시장 추종"},
        {"지수": "전세계 주식", "티커": "SPGM", "운용사": "State Street Global Advisors", "종목명": "SPDR Portfolio MSCI Global Stock Market ETF", "의미": "전세계 주식시장 광범위 분산 추종"},
        {"지수": "미국 제외 전세계", "티커": "VXUS", "운용사": "Vanguard", "종목명": "Vanguard Total International Stock ETF", "의미": "미국을 제외한 글로벌 주식시장 추종"},
        {"지수": "미국 제외 전세계", "티커": "IXUS", "운용사": "BlackRock iShares", "종목명": "iShares Core MSCI Total International Stock ETF", "의미": "미국 제외 선진국과 신흥국 주식시장 추종"},
        {"지수": "미국 제외 선진국", "티커": "VEA", "운용사": "Vanguard", "종목명": "Vanguard FTSE Developed Markets ETF", "의미": "미국을 제외한 선진국 주식시장 추종"},
        {"지수": "신흥국", "티커": "VWO", "운용사": "Vanguard", "종목명": "Vanguard FTSE Emerging Markets ETF", "의미": "신흥국 주식시장 추종"},
        {"지수": "글로벌 대형주", "티커": "IOO", "운용사": "BlackRock iShares", "종목명": "iShares Global 100 ETF", "의미": "글로벌 대형 우량주 100개 기업 추종"},
    ],
    "미국 섹터 ETF (11개)": [
        {"티커": "XLB", "종목명": "Materials Select Sector SPDR Fund", "구분": "소재", "의미": "미국 소재 섹터 추종"},
        {"티커": "XLC", "종목명": "Communication Services Select Sector SPDR Fund", "구분": "커뮤니케이션", "의미": "미국 커뮤니케이션 서비스 섹터 추종"},
        {"티커": "XLY", "종목명": "Consumer Discretionary Select Sector SPDR Fund", "구분": "경기소비재", "의미": "미국 경기소비재 섹터 추종"},
        {"티커": "XLP", "종목명": "Consumer Staples Select Sector SPDR Fund", "구분": "필수소비재", "의미": "미국 필수소비재 섹터 추종"},
        {"티커": "XLE", "종목명": "Energy Select Sector SPDR Fund", "구분": "에너지", "의미": "미국 에너지 섹터 추종"},
        {"티커": "XLF", "종목명": "Financial Select Sector SPDR Fund", "구분": "금융", "의미": "미국 금융 섹터 추종"},
        {"티커": "XLV", "종목명": "Health Care Select Sector SPDR Fund", "구분": "헬스케어", "의미": "미국 헬스케어 섹터 추종"},
        {"티커": "XLI", "종목명": "Industrial Select Sector SPDR Fund", "구분": "산업재", "의미": "미국 산업재 섹터 추종"},
        {"티커": "XLRE", "종목명": "Real Estate Select Sector SPDR Fund", "구분": "부동산", "의미": "미국 부동산 섹터 추종"},
        {"티커": "XLK", "종목명": "Technology Select Sector SPDR Fund", "구분": "기술", "의미": "미국 기술 섹터 추종"},
        {"티커": "XLU", "종목명": "Utilities Select Sector SPDR Fund", "구분": "유틸리티", "의미": "미국 유틸리티 섹터 추종"},
    ],
    "위험회피 심리": [
        {"티커": "TLT", "종목명": "iShares 20+ Year Treasury Bond ETF", "구분": "장기국채", "의미": "위험회피 때 선호되는 미국 장기국채 추종"},
        {"티커": "IEF", "종목명": "iShares 7-10 Year Treasury Bond ETF", "구분": "중기국채", "의미": "미국 중기국채 추종"},
        {"티커": "SHY", "종목명": "iShares 1-3 Year Treasury Bond ETF", "구분": "단기국채", "의미": "미국 단기국채 추종"},
        {"티커": "GLD", "종목명": "SPDR Gold Shares", "구분": "금", "의미": "대표 안전자산인 금 가격 추종"},
        {"티커": "UUP", "종목명": "Invesco DB US Dollar Index Bullish Fund", "구분": "달러", "의미": "미국 달러 강세 추종"},
    ],
    "한국 대표 지수 ETF": [
        {"지수": "KOSPI 200", "티커": "069500", "운용사": "삼성자산운용", "종목명": "KODEX 200", "의미": "한국 대형주 대표, 시장 전체 흐름 확인용"},
        {"지수": "KOSPI 200", "티커": "102110", "운용사": "미래에셋자산운용", "종목명": "TIGER 200", "의미": "한국 대형주 대표, 시장 전체 흐름 확인용"},
        {"지수": "KOSPI 200", "티커": "152100", "운용사": "KB자산운용", "종목명": "KBSTAR 200", "의미": "한국 대형주 대표, 시장 전체 흐름 확인용"},
        {"지수": "KOSDAQ 150", "티커": "229200", "운용사": "삼성자산운용", "종목명": "KODEX 코스닥150", "의미": "한국 성장주 대표, 코스닥 시장 흐름 확인용"},
        {"지수": "KOSDAQ 150", "티커": "232080", "운용사": "미래에셋자산운용", "종목명": "TIGER 코스닥150", "의미": "한국 성장주 대표, 코스닥 시장 흐름 확인용"},
        {"지수": "KOSPI 200 레버리지", "티커": "122630", "운용사": "삼성자산운용", "종목명": "KODEX 레버리지", "의미": "위험선호 심리 확인용"},
        {"지수": "KOSPI 200 인버스", "티커": "114800", "운용사": "삼성자산운용", "종목명": "KODEX 인버스", "의미": "위험회피 심리 확인용"},
    ],
    "한국 주요 섹터 ETF": [
        {"티커": "091160", "종목명": "KODEX 반도체", "구분": "반도체", "의미": "한국 반도체 섹터 추종"},
        {"티커": "091230", "종목명": "TIGER 반도체", "구분": "반도체", "의미": "한국 반도체 섹터 추종"},
        {"티커": "305540", "종목명": "TIGER 2차전지테마", "구분": "2차전지", "의미": "한국 2차전지 테마 추종"},
        {"티커": "305720", "종목명": "KODEX 2차전지산업", "구분": "2차전지", "의미": "한국 2차전지 산업 추종"},
        {"티커": "228800", "종목명": "TIGER 자동차", "구분": "자동차", "의미": "한국 자동차 섹터 추종"},
        {"티커": "091170", "종목명": "KODEX 은행", "구분": "은행", "의미": "한국 은행 섹터 추종"},
        {"티커": "244580", "종목명": "KODEX 바이오", "구분": "바이오", "의미": "한국 바이오 섹터 추종"},
    ],
}

DUAL_MOMENTUM_ASSET_PRESETS = [
    ("주식 (지역별)", "SPY", "미국 S&P500"),
    ("주식 (지역별)", "QQQ", "미국 나스닥100"),
    ("주식 (지역별)", "EFA", "미국 제외 선진국"),
    ("주식 (지역별)", "EEM", "신흥국"),
    ("주식 (지역별)", "VWO", "신흥국 (뱅가드)"),
    ("주식 (지역별)", "EWJ", "일본"),
    ("주식 (지역별)", "MCHI", "중국"),
    ("채권 (안전자산/피신처)", "BIL", "초단기 미국채 (1-3개월)"),
    ("채권 (안전자산/피신처)", "SHY", "단기 미국채 (1-3년)"),
    ("채권 (안전자산/피신처)", "IEF", "중기 미국채 (7-10년)"),
    ("채권 (안전자산/피신처)", "TLT", "장기 미국채 (20년+)"),
    ("채권 (안전자산/피신처)", "AGG", "미국 종합채권"),
    ("대안자산", "GLD", "금"),
    ("대안자산", "IAU", "금 (저비용)"),
    ("대안자산", "VNQ", "미국 리츠"),
    ("대안자산", "DJP", "원자재"),
]

DUAL_MOMENTUM_ASSET_OPTIONS = [
    f"{category} | {ticker} - {name}"
    for category, ticker, name in DUAL_MOMENTUM_ASSET_PRESETS
]
DUAL_MOMENTUM_ASSET_OPTIONS.append("직접 입력")
DUAL_MOMENTUM_TICKER_BY_OPTION = {
    option: ticker
    for option, (_, ticker, _) in zip(DUAL_MOMENTUM_ASSET_OPTIONS, DUAL_MOMENTUM_ASSET_PRESETS)
}


def configure_yfinance_cache(yf):
    """yfinance가 쓰는 로컬 캐시를 프로젝트 내부로 고정합니다."""
    cache_dir = Path(__file__).resolve().parents[1] / ".cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))


def format_yfinance_date(date_text):
    """YYYYMMDD 입력값을 yfinance가 받는 YYYY-MM-DD 형식으로 바꿉니다."""
    date_text = str(date_text).strip()
    if len(date_text) != 8 or not date_text.isdigit():
        raise ValueError("날짜는 YYYYMMDD 형식의 숫자 8자리여야 합니다.")
    return f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}"


def normalize_yfinance_ohlcv(df):
    """yfinance OHLCV 결과를 대시보드 내부 컬럼명으로 정규화합니다."""
    if df is None or df.empty:
        return pd.DataFrame()

    normalized = df.copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [col[0] for col in normalized.columns]

    normalized = normalized.rename(columns={
        'Open': '시가',
        'High': '고가',
        'Low': '저가',
        'Close': '종가',
        'Adj Close': '수정종가',
        'Volume': '거래량',
        'Dividends': '배당금',
    })

    required_columns = ['시가', '고가', '저가', '종가', '거래량']
    if not all(column in normalized.columns for column in required_columns):
        return pd.DataFrame()

    normalized = normalized.dropna(subset=['시가', '고가', '저가', '종가'])
    if normalized.empty:
        return pd.DataFrame()

    normalized.index = pd.to_datetime(normalized.index).tz_localize(None)
    if '배당금' not in normalized.columns:
        normalized['배당금'] = 0.0
    return normalized


def download_yfinance_ohlcv(yf, ticker_symbol, start_yf, end_yf):
    """download 실패 시 Ticker.history로 한 번 더 재시도합니다."""
    df = yf.download(
        ticker_symbol,
        start=start_yf,
        end=end_yf,
        progress=False,
        auto_adjust=False,
        threads=False,
    )
    normalized = normalize_yfinance_ohlcv(df)
    if not normalized.empty:
        return normalized

    ticker_obj = yf.Ticker(ticker_symbol)
    history_df = ticker_obj.history(
        start=start_yf,
        end=end_yf,
        auto_adjust=False,
        actions=True,
    )
    return normalize_yfinance_ohlcv(history_df)


def normalize_search_text(value):
    return "".join(value.strip().lower().replace("-", " ").split())


def resolve_ticker_input(ticker_input):
    """회사명/별칭/영문 공식명을 실제 조회용 종목코드로 변환합니다. 수동 별칭 매칭 후 실시간 DB 완전/부분 매칭을 수행합니다."""
    if not ticker_input:
        return ""
    
    # 1. 수동 별칭 사전을 활용한 빠른 조회
    key = normalize_search_text(ticker_input)
    if key in KOREAN_TICKER_ALIASES:
        return KOREAN_TICKER_ALIASES[key]

    # 2. KIND + Naver ETF 통합 목록에서 완전 일치 혹은 지능형 부분 매칭
    listed_df = get_all_listed_stocks()
    if not listed_df.empty:
        target_name = ticker_input.strip().lower().replace(" ", "")
        
        # 완전 일치 조회
        matched_rows = listed_df[listed_df['name'].str.lower().str.replace(" ", "") == target_name]
        if not matched_rows.empty:
            return matched_rows.iloc[0]['ticker']
            
        # 부분 일치 조회 (가장 짧은 이름 우선 매칭)
        matched_part = listed_df[listed_df['name'].str.lower().str.replace(" ", "").str.contains(target_name, na=False)]
        if not matched_part.empty:
            matched_part = matched_part.copy()
            matched_part['name_len'] = matched_part['name'].str.len()
            matched_part = matched_part.sort_values(by='name_len')
            return matched_part.iloc[0]['ticker']

    # 3. 매칭 실패 시 입력값 그대로 반환
    return ticker_input.strip()

# [LOG: 20260604_1508]
# 실시간 KIND 및 Naver ETF API를 활용한 전 상장사 및 ETF 통합 로딩 및 캐싱 기능 도입 (로컬 CSV 백업 Fallback 지원)
@st.cache_data(ttl=86400)
def get_all_listed_stocks():
    """KIND(기업공시채널)에서 한국 거래소 전체 상장사 목록 및 네이버 금융에서 전체 ETF 목록을 가져와 병합합니다.
    네트워크 장애 시 로컬 백업 파일(listed_stocks_backup.csv)에서 불러와 안정적인 검색을 상시 지원합니다.
    """
    import requests
    from io import BytesIO
    
    backup_path = Path(__file__).parent / "listed_stocks_backup.csv"
    df_stocks = pd.DataFrame()
    df_etfs = pd.DataFrame()
    
    # 1. KIND 일반 상장 주식 로드
    url_kind = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download'
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url_kind, headers=headers, timeout=5)
        df_stocks = pd.read_html(BytesIO(res.content), encoding='cp949', flavor='lxml')[0]
        df_stocks['종목코드'] = df_stocks['종목코드'].astype(str).str.zfill(6)
        df_stocks['회사명'] = df_stocks['회사명'].str.strip()
        df_stocks = df_stocks[['회사명', '종목코드']].rename(columns={'회사명': 'name', '종목코드': 'ticker'})
    except Exception:
        pass

    # 2. 네이버 금융 ETF 목록 로드 (배당plus, 고배당, S&P500 등 ETF 검색 지원)
    url_etf = 'https://finance.naver.com/api/sise/etfItemList.nhn'
    try:
        res = requests.get(url_etf, timeout=5)
        data = res.json()
        etf_list = data.get('result', {}).get('etfItemList', [])
        if etf_list:
            temp_list = []
            for item in etf_list:
                temp_list.append({
                    'name': item.get('itemname', '').strip(),
                    'ticker': item.get('itemcode', '').strip().zfill(6)
                })
            df_etfs = pd.DataFrame(temp_list)
    except Exception:
        pass

    # 3. 주식 및 ETF 병합
    df_merged = pd.DataFrame()
    if not df_stocks.empty or not df_etfs.empty:
        if df_stocks.empty:
            df_merged = df_etfs
        elif df_etfs.empty:
            df_merged = df_stocks
        else:
            df_merged = pd.concat([df_stocks, df_etfs], ignore_index=True)

    # 4. 성공적으로 가져왔다면 로컬 백업 파일 갱신
    if not df_merged.empty:
        try:
            df_merged.to_csv(backup_path, index=False, encoding='utf-8-sig')
        except Exception:
            pass
        return df_merged

    # 5. 네트워크 에러로 둘 다 실패 시 로컬 백업 파일 로드 시도
    if backup_path.exists():
        try:
            df_backup = pd.read_csv(backup_path, dtype={'ticker': str})
            df_backup['ticker'] = df_backup['ticker'].astype(str).str.zfill(6)
            return df_backup
        except Exception:
            pass

    return pd.DataFrame()


def search_local_tickers(query):
    """부분 종목명/영문 별칭으로 로컬 카탈로그 및 KIND/Naver ETF 상장 목록에서 검색 후보를 찾습니다.
    한/영 대기업 그룹명 치환 매칭(예: lg <-> 엘지)을 기본 지원합니다.
    """
    key = normalize_search_text(query)
    if not key:
        return []

    # 한글과 영문/숫자가 붙어있는 경우(예: '배당plus')를 대비하여 토큰 단위 분리
    import re
    tokens = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+|[가-힣]+', key) if t]
    if not tokens:
        tokens = [key.lower()]

    # 대표적인 영문 그룹사 약어와 한글 공식 사명 매핑
    group_translation = {
        "lg": "엘지",
        "sk": "에스케이",
        "gs": "지에스",
        "cj": "씨제이",
        "hd": "현대",
    }

    # 토큰과 텍스트를 대조하여 매칭 여부를 판단하는 헬퍼 함수
    def match_tokens(target_text):
        if not isinstance(target_text, str):
            return False
        text_lower = target_text.lower().replace(" ", "")
        
        for token in tokens:
            translated = group_translation.get(token, None)
            if translated:
                if (token not in text_lower) and (translated not in text_lower):
                    return False
            else:
                reverse_match = False
                for eng, kor in group_translation.items():
                    if token == kor and eng in text_lower:
                        reverse_match = True
                        break
                if not reverse_match and (token not in text_lower):
                    return False
        return True

    matches = []
    
    # 1. 정적 로컬 카탈로그 검색 (ETF 등 수동 캐싱 우선)
    for ticker, item in LOCAL_TICKER_CATALOG.items():
        searchable_values = [ticker, item["name"], *item.get("aliases", [])]
        for val in searchable_values:
            if match_tokens(val):
                matches.append({"ticker": ticker, "name": item["name"]})
                break

    # 2. KIND + Naver ETF 통합 목록 실시간 검색 (AND 토큰 검색)
    listed_df = get_all_listed_stocks()
    if not listed_df.empty:
        filtered = listed_df[listed_df['name'].apply(match_tokens)]
        for _, row in filtered.iterrows():
            ticker = row['ticker']
            name = row['name']
            if not any(m['ticker'] == ticker for m in matches):
                matches.append({"ticker": ticker, "name": name})

    # 3. 정렬 순서 최적화: 검색어 기반 스마트 정렬 (Score System)
    # 0순위: 완전 일치, 1순위: 검색어로 시작함, 2순위: 검색어 포함, 3순위: 그 외
    def score_match(query_str, name_str):
        q = query_str.lower().replace(" ", "")
        n = name_str.lower().replace(" ", "")
        translated_q = group_translation.get(q, None)
        
        if q == n or (translated_q and translated_q == n):
            return 0
        elif n.startswith(q) or (translated_q and n.startswith(translated_q)):
            return 1
        elif q in n or (translated_q and translated_q in n):
            return 2
        return 3

    matches = sorted(matches, key=lambda x: (score_match(key, x['name']), len(x['name']), x['name']))

    return matches


def get_ticker_name(ticker_code):
    """종목 코드를 받아 종목명을 반환합니다. (KIND/Naver ETF DB 조회 -> yfinance -> pykrx 순)"""
    ticker_code = ticker_code.strip()
    if not ticker_code:
        return UNKNOWN_TICKER_NAME
    
    # 영문 티커 기호(미국 주식)는 오직 ASCII 알파벳이어야 하고, 한국 주식은 6자리 숫자여야 합니다. (한글 검색어 패스 차단)
    is_valid_us_ticker = ticker_code.isascii() and ticker_code.isalpha()
    is_valid_kr_ticker = len(ticker_code) == 6 and ticker_code.isdigit()
    if not (is_valid_us_ticker or is_valid_kr_ticker):
        return UNKNOWN_TICKER_NAME
    
    if ticker_code in LOCAL_TICKER_CATALOG:
        return LOCAL_TICKER_CATALOG[ticker_code]["name"]
        
    # 1. KIND + Naver ETF 전체 상장사 목록 검색 (가장 안정적)
    listed_df = get_all_listed_stocks()
    if not listed_df.empty:
        match = listed_df[listed_df['ticker'] == ticker_code]
        if not match.empty:
            return match.iloc[0]['name']

    # 2. 영어 종목코드 (미국 주식)인 경우 yfinance로 조회
    if ticker_code.isalpha():
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            ticker_info = yf.Ticker(ticker_code.upper()).info
            name = ticker_info.get('longName') or ticker_info.get('shortName')
            if name:
                return name
        except Exception:
            pass
        return UNKNOWN_TICKER_NAME
            
    # 3. pykrx 백업 시도
    try:
        name = stock.get_market_ticker_name(ticker_code)
        if name != "":
            return name
    except Exception:
        pass
        
    # 4. yfinance 한국 소스(.KS / .KQ) 백업 조회
    for suffix in [".KS", ".KQ"]:
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            ticker_info = yf.Ticker(f"{ticker_code}{suffix}").info
            name = ticker_info.get('longName') or ticker_info.get('shortName')
            if name:
                return name
        except Exception:
            pass
        
    return UNKNOWN_TICKER_NAME


@st.cache_data
def load_data(start_date, end_date, ticker_code):
    """선택한 종목의 주식 데이터를 불러옵니다. pykrx 연결장애 시 yfinance 한국소스로 우아하게 대체합니다."""
    ticker_code = ticker_code.strip()
    
    # 1. 영어 종목코드 (미국 주식)인 경우 yfinance로 즉시 로딩
    if ticker_code.isalpha():
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            start_yf = format_yfinance_date(start_date)
            end_yf = format_yfinance_date(end_date)
            df = download_yfinance_ohlcv(yf, ticker_code.upper(), start_yf, end_yf)
            if not df.empty:
                return df
        except Exception as e:
            st.error(f"미국 주식 yfinance 데이터 로드 실패: {e}")
            return pd.DataFrame()
            
    # 2. 한국 주식/ETF (숫자 코드) 데이터 로드
    # pykrx의 잦은 차단/장애(EXPECTING VALUE 에러)를 방어하기 위해 yfinance(.KS/.KQ)를 최우선으로 다운로드합니다.
    if len(ticker_code) == 6 and ticker_code.isdigit():
        start_yf = format_yfinance_date(start_date)
        end_yf = format_yfinance_date(end_date)
        
        for suffix in [".KS", ".KQ"]:
            try:
                import yfinance as yf
                configure_yfinance_cache(yf)
                df = download_yfinance_ohlcv(yf, f"{ticker_code}{suffix}", start_yf, end_yf)
                if not df.empty:
                    return df
            except Exception:
                pass
                
    # 3. 마지막 백업 수단: pykrx
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker_code)
        if not df.empty:
            return df
    except Exception:
        pass
        
    return pd.DataFrame()


# [LOG: 20260604_1751]
# 2-2. 주요 재무 데이터 로드 함수 (yfinance 연동)
@st.cache_data
def load_financial_data(ticker_code):
    """yfinance를 활용하여 해당 종목의 연간 재무 정보를 로드합니다."""
    import yfinance as yf
    configure_yfinance_cache(yf)
    
    # 한국 주식 코드(6자리 숫자)의 경우 접미사 처리
    tickers_to_try = [ticker_code]
    if len(ticker_code) == 6 and ticker_code.isdigit():
        tickers_to_try = [f"{ticker_code}.KS", f"{ticker_code}.KQ"]
        
    for ticker_symbol in tickers_to_try:
        try:
            tic = yf.Ticker(ticker_symbol)
            # 연간 재무 상태표 (balance_sheet) & 손익계산서 (financials) & 현금흐름표 (cashflow)
            bs = tic.balance_sheet
            fin = tic.financials
            cf = tic.cashflow
            
            combined_data = {}
            
            # balance_sheet 항목
            if bs is not None and not bs.empty:
                for item in [
                    'Total Assets',
                    'Current Assets',
                    'Cash And Cash Equivalents',
                    'Accounts Receivable',
                    'Inventory',
                    'Net PPE',
                    'Total Liabilities Net Minority Interest',
                    'Current Liabilities',
                    'Accounts Payable',
                    'Total Debt',
                    'Net Debt',
                    'Stockholders Equity',
                ]:
                    if item in bs.index:
                        combined_data[item] = bs.loc[item]
            
            # financials 항목
            if fin is not None and not fin.empty:
                for item in [
                    'Total Revenue',
                    'Cost Of Revenue',
                    'Gross Profit',
                    'Research And Development',
                    'Selling General And Administration',
                    'Operating Income',
                    'EBITDA',
                    'EBIT',
                    'Pretax Income',
                    'Tax Provision',
                    'Net Income',
                    'Basic EPS',
                    'Diluted EPS',
                ]:
                    if item in fin.index:
                        combined_data[item] = fin.loc[item]
                        
            # cashflow 항목
            if cf is not None and not cf.empty:
                for item in [
                    'Operating Cash Flow',
                    'Investing Cash Flow',
                    'Financing Cash Flow',
                    'Capital Expenditure',
                    'Free Cash Flow',
                    'Repurchase Of Capital Stock',
                    'Cash Dividends Paid',
                ]:
                    if item in cf.index:
                        combined_data[item] = cf.loc[item]
            
            if combined_data:
                # 데이터프레임 빌드 (행: 연도, 열: 재무항목)
                df_fin = pd.DataFrame(combined_data)

                formatted_index = []
                for idx in df_fin.index:
                    try:
                        formatted_index.append(pd.to_datetime(idx).strftime('%Y년'))
                    except Exception:
                        formatted_index.append(str(idx))
                df_fin.index = formatted_index

                df_fin = df_fin.rename(columns=FINANCIALS_KR)
                return df_fin.dropna(axis=1, how='all')
        except Exception:
            continue
                
    return pd.DataFrame()


def format_metric_value(value, value_type):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    if value_type == 'percent':
        return f"{value * 100:.2f}%"
    if value_type == 'yield_percent':
        return f"{value:.2f}%" if abs(value) > 0.2 else f"{value * 100:.2f}%"
    if value_type == 'large':
        return f"{value:,.0f}"
    return f"{value:,.2f}"


@st.cache_data
def load_key_metrics_data(ticker_code, cache_version=KEY_METRICS_CACHE_VERSION):
    """yfinance Ticker.info 기반 투자 지표를 가져옵니다."""
    import yfinance as yf
    configure_yfinance_cache(yf)

    tickers_to_try = [ticker_code]
    if len(ticker_code) == 6 and ticker_code.isdigit():
        tickers_to_try = [f"{ticker_code}.KS", f"{ticker_code}.KQ"]

    info = {}
    ticker_obj = None
    for ticker_symbol in tickers_to_try:
        try:
            candidate_ticker = yf.Ticker(ticker_symbol)
            candidate_info = candidate_ticker.info
            if candidate_info and candidate_info.get("quoteType"):
                info = candidate_info
                ticker_obj = candidate_ticker
                break
        except Exception:
            continue

    if not info:
        return pd.DataFrame()

    values = dict(info)
    value_sources = {key: "Yahoo info" for key, value in values.items() if value is not None}
    try:
        bs = ticker_obj.balance_sheet if ticker_obj is not None else pd.DataFrame()
        fin = ticker_obj.financials if ticker_obj is not None else pd.DataFrame()
        cf = ticker_obj.cashflow if ticker_obj is not None else pd.DataFrame()

        latest_equity = bs.loc['Stockholders Equity'].dropna().iloc[0] if 'Stockholders Equity' in bs.index else None
        latest_assets = bs.loc['Total Assets'].dropna().iloc[0] if 'Total Assets' in bs.index else None
        latest_revenue = fin.loc['Total Revenue'].dropna().iloc[0] if 'Total Revenue' in fin.index else None
        latest_operating_income = fin.loc['Operating Income'].dropna().iloc[0] if 'Operating Income' in fin.index else None
        latest_net_income = fin.loc['Net Income'].dropna().iloc[0] if 'Net Income' in fin.index else None
        latest_ebitda = fin.loc['EBITDA'].dropna().iloc[0] if 'EBITDA' in fin.index else None
        market_cap = values.get('marketCap')
        enterprise_value = values.get('enterpriseValue')

        if values.get('priceToBook') is None and market_cap and latest_equity:
            values['priceToBook'] = market_cap / latest_equity
            value_sources['priceToBook'] = '계산: 시가총액/자본총계'
        if values.get('returnOnEquity') is None and latest_net_income and latest_equity:
            values['returnOnEquity'] = latest_net_income / latest_equity
            value_sources['returnOnEquity'] = '계산: 순이익/자본총계'
        if values.get('returnOnAssets') is None and latest_net_income and latest_assets:
            values['returnOnAssets'] = latest_net_income / latest_assets
            value_sources['returnOnAssets'] = '계산: 순이익/총자산'
        if values.get('profitMargins') is None and latest_net_income and latest_revenue:
            values['profitMargins'] = latest_net_income / latest_revenue
            value_sources['profitMargins'] = '계산: 순이익/매출'
        if values.get('operatingMargins') is None and latest_operating_income and latest_revenue:
            values['operatingMargins'] = latest_operating_income / latest_revenue
            value_sources['operatingMargins'] = '계산: 영업이익/매출'
        if values.get('enterpriseToEbitda') is None and enterprise_value and latest_ebitda:
            values['enterpriseToEbitda'] = enterprise_value / latest_ebitda
            value_sources['enterpriseToEbitda'] = '계산: EV/EBITDA'
        if values.get('trailingPE') is None and market_cap and latest_net_income:
            values['trailingPE'] = market_cap / latest_net_income
            value_sources['trailingPE'] = '계산: 시가총액/순이익'
        if values.get('freeCashflow') is None and 'Free Cash Flow' in cf.index:
            values['freeCashflow'] = cf.loc['Free Cash Flow'].dropna().iloc[0]
            value_sources['freeCashflow'] = 'Yahoo cashflow'
        if values.get('operatingCashflow') is None and 'Operating Cash Flow' in cf.index:
            values['operatingCashflow'] = cf.loc['Operating Cash Flow'].dropna().iloc[0]
            value_sources['operatingCashflow'] = 'Yahoo cashflow'
    except Exception:
        pass

    rows = []
    for key in CORE_METRIC_KEYS:
        label, value_type = KEY_METRICS[key]
        value = values.get(key)
        rows.append({
            '구분': '핵심',
            '항목': label,
            '값': format_metric_value(value, value_type) if value is not None else '데이터 없음',
            '원본키': key,
            '출처': value_sources.get(key, '없음'),
        })

    for key, (label, value_type) in KEY_METRICS.items():
        if key in CORE_METRIC_KEYS:
            continue
        value = values.get(key)
        if value is None:
            continue
        rows.append({
            '구분': '추가',
            '항목': label,
            '값': format_metric_value(value, value_type),
            '원본키': key,
            '출처': value_sources.get(key, 'Yahoo info'),
        })

    return pd.DataFrame(rows)


@st.cache_data
def load_fund_profile_data(ticker_code):
    """ETF/펀드처럼 재무제표가 없는 종목의 기본 정보를 가져옵니다."""
    import yfinance as yf
    configure_yfinance_cache(yf)

    try:
        info = yf.Ticker(ticker_code).info
    except Exception:
        return pd.DataFrame()

    profile_items = {
        'longName': '상품명',
        'category': '분류',
        'fundFamily': '운용사',
        'totalAssets': '순자산',
        'navPrice': 'NAV',
        'yield': '분배수익률',
        'annualReportExpenseRatio': '총보수율',
        'beta3Year': '3년 베타',
        'threeYearAverageReturn': '3년 평균수익률',
        'fiveYearAverageReturn': '5년 평균수익률',
        'fiftyTwoWeekLow': '52주 최저가',
        'fiftyTwoWeekHigh': '52주 최고가',
    }
    rows = []
    for key, label in profile_items.items():
        value = info.get(key)
        if value is not None:
            rows.append({'항목': label, '값': value})

    return pd.DataFrame(rows)


def render_clipboard_copy_button(copy_text, button_label="📋 전체 재무정보 복사"):
    """브라우저 클립보드로 TSV 텍스트를 복사하는 작은 버튼을 렌더링합니다."""
    if not copy_text.strip():
        return

    button_id = f"copy-financial-{abs(hash(copy_text))}"
    payload = json.dumps(copy_text, ensure_ascii=False)
    components.html(
        f"""
        <button id="{button_id}" style="
            border: 1px solid #d0d7de;
            background: #ffffff;
            border-radius: 6px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 13px;
        ">{button_label}</button>
        <span id="{button_id}-status" style="margin-left:8px;color:#57606a;font-size:12px;"></span>
        <script>
        const button = document.getElementById("{button_id}");
        const status = document.getElementById("{button_id}-status");
        button.onclick = async () => {{
            try {{
                await navigator.clipboard.writeText({payload});
                status.textContent = "복사됨";
            }} catch (error) {{
                status.textContent = "복사 실패";
            }}
        }};
        </script>
        """,
        height=42,
    )


def build_financial_copy_text(ticker_code, ticker_name, metrics_df, financial_df, profile_df):
    parts = []
    parts.append("종목 정보")
    parts.append(pd.DataFrame([{
        "종목명": ticker_name,
        "티커": ticker_code,
    }]).to_csv(sep="\t", index=False))
    if metrics_df is not None and not metrics_df.empty:
        parts.append("투자 지표 요약")
        parts.append(metrics_df.to_csv(sep="\t", index=False))
    if financial_df is not None and not financial_df.empty:
        parts.append("연간 재무제표")
        parts.append(financial_df.reset_index(names='연도').to_csv(sep="\t", index=False))
    if profile_df is not None and not profile_df.empty:
        parts.append("ETF/펀드 기본정보")
        parts.append(profile_df.to_csv(sep="\t", index=False))
    return "\n".join(parts)


def render_financial_data_section(ticker_code, ticker_name):
    """선택된 종목의 주요 재무 정보를 화면에 표시합니다."""
    with st.spinner("재무 정보 데이터를 불러오는 중..."):
        metrics_df = load_key_metrics_data(ticker_code)
        df_financials = load_financial_data(ticker_code)
        fund_profile = pd.DataFrame()
        copy_financials = pd.DataFrame()

        if not df_financials.empty:
            copy_financials = df_financials.copy()
        else:
            fund_profile = load_fund_profile_data(ticker_code)

        copy_text = build_financial_copy_text(ticker_code, ticker_name, metrics_df, copy_financials, fund_profile)

    title_col, copy_col = st.columns([4, 1.2])
    with title_col:
        st.subheader(f"🏢 {ticker_name} ({ticker_code}) 주요 재무 정보")
    with copy_col:
        render_clipboard_copy_button(copy_text)

    with st.container():
        if not metrics_df.empty:
            st.write("📌 **투자 지표 요약**")
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        if not df_financials.empty:
            display_fin = df_financials.copy()

            for col in display_fin.columns:
                try:
                    display_fin[col] = display_fin[col].map(
                        lambda x: f"{x:,.0f}" if pd.notnull(x) and not isinstance(x, str) else x
                    )
                except Exception:
                    pass

            st.write("📊 **연간 재무제표**")
            st.dataframe(display_fin, use_container_width=True)
            st.caption("※ 정보 제공: Yahoo Finance (연간 기준 재무 데이터)")
        else:
            if not fund_profile.empty:
                display_profile = fund_profile.copy()
                display_profile['값'] = display_profile['값'].map(
                    lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and abs(x) >= 1000
                    else f"{x:.2%}" if isinstance(x, (int, float)) and 0 < abs(x) < 1
                    else x
                )
                fund_profile = display_profile
                st.write("📄 **ETF/펀드 기본정보**")
                st.dataframe(display_profile, use_container_width=True, hide_index=True)
                st.caption("※ 이 종목은 ETF/펀드 성격이라 기업 재무제표 대신 Yahoo Finance 기본정보를 표시합니다.")
            else:
                st.info("이 종목에 대한 연간 재무 정보(재무상태표/손익계산서/현금흐름표)를 불러올 수 없습니다.")


# 3. 머신러닝 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

# 4. 머신러닝 롤링 윈도우 예측 수행 함수
@st.cache_data(show_spinner=False)
def run_rolling_forecast(X, y, window_size, _progress_container=None):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 종가를 예측합니다. 
    동일한 피처와 윈도우 크기일 경우 연산 결과를 캐싱하여 즉시 반환합니다.
    """
    predictions = []
    prediction_dates = []
    
    # 진행 상황 표시줄
    progress_target = _progress_container or st
    progress_bar = progress_target.progress(0)
    status_text = progress_target.empty()
    
    total_steps = len(X) - window_size
    
    for i in range(window_size, len(X)):
        # 학습 데이터 슬라이싱
        X_train = X.iloc[i-window_size:i]
        y_train = y.iloc[i-window_size:i]
        
        # 예측 대상 하루
        X_test = X.iloc[[i]]
        
        # 모델 생성 및 학습
        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # 예측 및 결과 저장
        pred = model.predict(X_test)[0]
        predictions.append(pred)
        prediction_dates.append(X.index[i])
        
        # 프로그레스바 업데이트
        current_step = i - window_size + 1
        progress_bar.progress(current_step / total_steps)
        status_text.text(f"머신러닝 예측 진행 중: {current_step}/{total_steps} 영업일 완료...")
        
    progress_bar.empty()
    status_text.empty()
    
    pred_series = pd.Series(predictions, index=prediction_dates)
    return pred_series

# 5. 머신러닝 백테스트 수익률 계산 함수 (실전 수수료/슬리피지 비용 반영)
def run_ml_backtest(df, pred_series, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """예측 결과를 기반으로 머신러닝 매매 백테스트 수익률을 계산합니다."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    backtest_df = pd.DataFrame({
        'Actual_Close': df['종가'].loc[pred_series.index],
        'Predicted_Close': pred_series,
        'Prev_Close': df['종가'].shift(1).loc[pred_series.index],
        '배당금': df['배당금'].loc[pred_series.index] if '배당금' in df.columns else 0.0
    }).dropna()
    
    backtest_df['Buy_Signal'] = backtest_df['Predicted_Close'] > backtest_df['Prev_Close']
    
    # 이전 영업일 매수 포지션 여부
    prev_signals = backtest_df['Buy_Signal'].shift(1).fillna(False)
    
    # 포지션 변동(진입/청산) 시 거래 비용 차감
    entry_cost = np.where((backtest_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((backtest_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
    total_cost = entry_cost + exit_cost
    
    # 배당 재투자 수익률 계산
    if use_drip and '배당금' in backtest_df.columns:
        div_yield = backtest_df['배당금'] / backtest_df['Prev_Close']
        # 보유하고 있는 날(Buy_Signal == True)에만 배당 수익률 가산
        strategy_div_yield = np.where(backtest_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
    
    # 전략 일별 수익률 계산
    backtest_df['Strategy_Return'] = np.where(
        backtest_df['Buy_Signal'],
        (backtest_df['Actual_Close'] / backtest_df['Prev_Close']) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    
    # 단순 보유 일별 수익률 (최초 1회 매수 수수료 반영 + 배당 수익률 반영)
    hold_returns = (backtest_df['Actual_Close'] / backtest_df['Prev_Close']) + div_yield
    hold_returns_array = hold_returns.values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    backtest_df['Hold_Return'] = hold_returns_array
    
    # 누적 수익률 계산 (%)
    backtest_df['Strategy_Cum_Return'] = (backtest_df['Strategy_Return'].cumprod() - 1) * 100
    backtest_df['Hold_Cum_Return'] = (backtest_df['Hold_Return'].cumprod() - 1) * 100
    
    # 최종 잔고 계산 (원)
    backtest_df['Strategy_Balance'] = initial_budget * backtest_df['Strategy_Return'].cumprod()
    backtest_df['Hold_Balance'] = initial_budget * backtest_df['Hold_Return'].cumprod()
    
    return backtest_df

# 6. 머신러닝 월별 백테스트 통계 계산 함수
def calculate_ml_monthly_stats(actual, predicted, backtest_df):
    """머신러닝 예측 오차 및 월별 수익률 통계를 계산합니다."""
    compare_df = pd.DataFrame({
        'Actual': actual,
        'Predicted': predicted,
        'Strategy_Return': backtest_df['Strategy_Return']
    }).dropna()
    
    compare_df['Absolute Error'] = (compare_df['Actual'] - compare_df['Predicted']).abs()
    compare_df['YearMonth'] = compare_df.index.strftime('%Y-%m')
    
    # 월별 MAE
    monthly_mae = compare_df.groupby('YearMonth')['Absolute Error'].mean().reset_index()
    monthly_mae.columns = ['년-월', '평균 절대 오차 (원)']
    
    # 월별 오차율(%)
    compare_df['Error Rate (%)'] = (compare_df['Absolute Error'] / compare_df['Actual']) * 100
    monthly_error_rate = compare_df.groupby('YearMonth')['Error Rate (%)'].mean().reset_index()
    monthly_error_rate.columns = ['년-월', '평균 오차율 (%)']
    
    # 월별 누적 수익률
    monthly_return = compare_df.groupby('YearMonth')['Strategy_Return'].prod().reset_index()
    monthly_return['Strategy_Return'] = (monthly_return['Strategy_Return'] - 1) * 100
    monthly_return.columns = ['년-월', '월간 수익률 (%)']
    
    stats_df = pd.merge(monthly_mae, monthly_error_rate, on='년-월')
    stats_df = pd.merge(stats_df, monthly_return, on='년-월')
    return stats_df

# 7. 변동성 돌파 전략 백테스트 계산 함수 (실전 수수료/슬리피지 비용 반영)
def run_vbt_backtest(df, K, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """변동성 돌파 전략 백테스트를 수행합니다. 
    매일 당일 진입 후 당일 청산하므로 신호 발생 시 왕복(2회) 거래 비용이 차감됩니다.
    """
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    round_trip_cost = 2 * cost_rate
    
    vbt_df = df.copy()
    
    # 변동성 폭 계산 (전일 고가 - 전일 저가)
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    
    # 매수 목표가 계산 (당일 시가 + 변동폭 * K)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    
    # 매수 조건: 당일 고가가 매수 목표가를 초과했는지 판별
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    # 전략 일별 수익률 계산 (매수 체결 시 당일 종가 / 매수 목표가 - 왕복 비용, 미체결 시 1.0)
    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        (vbt_df['종가'] / vbt_df['Buy_Target']) - round_trip_cost,
        1.0
    )
    
    # 배당금 반영
    if use_drip and '배당금' in vbt_df.columns:
        div_yield = vbt_df['배당금'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])
    else:
        div_yield = 0.0
    
    # 단순 보유(Buy & Hold) 일별 수익률 (최초 1회 매수 수수료 반영 + 배당 수익률 반영)
    hold_returns = (vbt_df['종가'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    vbt_df['Hold_Return'] = hold_returns_array
    
    # 누적 수익률 계산 (%)
    vbt_df['Strategy_Cum_Return'] = (vbt_df['Strategy_Return'].cumprod() - 1) * 100
    vbt_df['Hold_Cum_Return'] = (vbt_df['Hold_Return'].cumprod() - 1) * 100
    
    # 최종 잔고 계산 (원)
    vbt_df['Strategy_Balance'] = initial_budget * vbt_df['Strategy_Return'].cumprod()
    vbt_df['Hold_Balance'] = initial_budget * vbt_df['Hold_Return'].cumprod()
    
    # 일별 수익률 변동 (%)
    vbt_df['Daily_Return_Pct'] = (vbt_df['Strategy_Return'] - 1) * 100
    
    return vbt_df

# 8. 변동성 돌파 전략 월별 백테스트 통계 계산 함수
def calculate_vbt_monthly_stats(vbt_df):
    """변동성 돌파 전략의 월간 매수 횟수 및 수익률 통계를 계산합니다."""
    stats_df = vbt_df.copy()
    stats_df['YearMonth'] = stats_df.index.strftime('%Y-%m')
    
    stats_df['Buy_Count'] = np.where(stats_df['Buy_Signal'], 1, 0)
    
    summary = stats_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    
    summary.columns = ['년-월', '매수 횟수 (회)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

# 9. 두 전략 월별 백테스트 요약 통계 계산 함수
def calculate_combined_monthly_stats(ml_df, vbt_df):
    """두 전략의 월별 수익률 및 머신러닝 오차율을 하나의 표로 통합하여 요약합니다."""
    # 1. 머신러닝 월별 요약
    ml_df['YearMonth'] = ml_df.index.strftime('%Y-%m')
    ml_df['Absolute Error'] = (ml_df['Actual_Close'] - ml_df['Predicted_Close']).abs()
    
    ml_summary = ml_df.groupby('YearMonth').agg({
        'Absolute Error': 'mean',
        'Strategy_Return': 'prod'
    }).reset_index()
    ml_summary.columns = ['년-월', '머신러닝 오차 (원)', 'ML_Return_Prod']
    
    # 2. 변동성 돌파 월별 요약
    vbt_df['YearMonth'] = vbt_df.index.strftime('%Y-%m')
    vbt_df['Buy_Count'] = np.where(vbt_df['Buy_Signal'], 1, 0)
    
    vbt_summary = vbt_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    vbt_summary.columns = ['년-월', '돌파 매수 횟수 (회)', 'VBT_Return_Prod', 'Hold_Return_Prod']
    
    # 3. 데이터 결합 및 백분율 변환
    merged = pd.merge(ml_summary, vbt_summary, on='년-월')
    merged['머신러닝 수익률 (%)'] = (merged['ML_Return_Prod'] - 1) * 100
    merged['변동성 돌파 수익률 (%)'] = (merged['VBT_Return_Prod'] - 1) * 100
    merged['단순 보유 수익률 (%)'] = (merged['Hold_Return_Prod'] - 1) * 100
    
    final_df = merged[['년-월', '머신러닝 수익률 (%)', '변동성 돌파 수익률 (%)', '단순 보유 수익률 (%)', '돌파 매수 횟수 (회)', '머신러닝 오차 (원)']]
    return final_df

# [LOG: 20260604_1725]
# 10. 이동평균선 골든크로스 전략 백테스트 함수
def run_ma_cross_backtest(df, short_period, long_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    ma_df = df.copy()
    ma_df['SMA_Short'] = ma_df['종가'].rolling(window=short_period).mean()
    ma_df['SMA_Long'] = ma_df['종가'].rolling(window=long_period).mean()
    
    ma_df['Buy_Signal'] = ma_df['SMA_Short'] > ma_df['SMA_Long']
    ma_df['Buy_Signal'] = np.where(pd.isna(ma_df['SMA_Long']), False, ma_df['Buy_Signal'])
    
    prev_signals = ma_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((ma_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((ma_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
    total_cost = entry_cost + exit_cost
    
    # 배당 재투자 수익률 계산
    if use_drip and '배당금' in ma_df.columns:
        div_yield = ma_df['배당금'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])
        strategy_div_yield = np.where(ma_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    ma_df['Strategy_Return'] = np.where(
        ma_df['Buy_Signal'],
        (ma_df['종가'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    ma_df['Strategy_Return'] = ma_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (ma_df['종가'] / ma_df['종가'].shift(1).fillna(ma_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    ma_df['Hold_Return'] = hold_returns_array
    
    ma_df['Strategy_Cum_Return'] = (ma_df['Strategy_Return'].cumprod() - 1) * 100
    ma_df['Hold_Cum_Return'] = (ma_df['Hold_Return'].cumprod() - 1) * 100
    ma_df['Strategy_Balance'] = initial_budget * ma_df['Strategy_Return'].cumprod()
    ma_df['Hold_Balance'] = initial_budget * ma_df['Hold_Return'].cumprod()
    
    ma_df['Daily_Return_Pct'] = (ma_df['Strategy_Return'] - 1) * 100
    return ma_df

def calculate_ma_cross_monthly_stats(ma_df):
    ma_df['YearMonth'] = ma_df.index.strftime('%Y-%m')
    ma_df['Buy_Count'] = np.where(ma_df['Buy_Signal'], 1, 0)
    summary = ma_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

# 11. RSI 과매도 반등 전략 백테스트 함수
def run_rsi_backtest(df, period, buy_rsi, sell_rsi, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    rsi_df = df.copy()
    delta = rsi_df['종가'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi_df['RSI'] = 100 - (100 / (1 + rs))
    
    signals = []
    position = False
    for r in rsi_df['RSI'].values:
        if pd.isna(r):
            signals.append(False)
        elif not position and r <= buy_rsi:
            position = True
            signals.append(True)
        elif position and r >= sell_rsi:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    rsi_df['Buy_Signal'] = signals
    prev_signals = rsi_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((rsi_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((rsi_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
    total_cost = entry_cost + exit_cost
    
    # 배당 재투자 수익률 계산
    if use_drip and '배당금' in rsi_df.columns:
        div_yield = rsi_df['배당금'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])
        strategy_div_yield = np.where(rsi_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    rsi_df['Strategy_Return'] = np.where(
        rsi_df['Buy_Signal'],
        (rsi_df['종가'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    rsi_df['Strategy_Return'] = rsi_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (rsi_df['종가'] / rsi_df['종가'].shift(1).fillna(rsi_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    rsi_df['Hold_Return'] = hold_returns_array
    
    rsi_df['Strategy_Cum_Return'] = (rsi_df['Strategy_Return'].cumprod() - 1) * 100
    rsi_df['Hold_Cum_Return'] = (rsi_df['Hold_Return'].cumprod() - 1) * 100
    rsi_df['Strategy_Balance'] = initial_budget * rsi_df['Strategy_Return'].cumprod()
    rsi_df['Hold_Balance'] = initial_budget * rsi_df['Hold_Return'].cumprod()
    
    rsi_df['Daily_Return_Pct'] = (rsi_df['Strategy_Return'] - 1) * 100
    return rsi_df

def calculate_rsi_monthly_stats(rsi_df):
    rsi_df['YearMonth'] = rsi_df.index.strftime('%Y-%m')
    rsi_df['Buy_Count'] = np.where(rsi_df['Buy_Signal'], 1, 0)
    summary = rsi_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary

# 12. 볼린저 밴드 반등 전략 백테스트 함수
def run_bollinger_backtest(df, period, std_dev, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    bb_df = df.copy()
    bb_df['Mid'] = bb_df['종가'].rolling(window=period).mean()
    bb_df['Std'] = bb_df['종가'].rolling(window=period).std()
    bb_df['Upper_Band'] = bb_df['Mid'] + (std_dev * bb_df['Std'])
    bb_df['Lower_Band'] = bb_df['Mid'] - (std_dev * bb_df['Std'])
    
    signals = []
    position = False
    closes = bb_df['종가'].values
    lowers = bb_df['Lower_Band'].values
    uppers = bb_df['Upper_Band'].values
    
    for i in range(len(bb_df)):
        c = closes[i]
        l = lowers[i]
        u = uppers[i]
        if pd.isna(l) or pd.isna(u):
            signals.append(False)
        elif not position and c <= l:
            position = True
            signals.append(True)
        elif position and c >= u:
            position = False
            signals.append(False)
        else:
            signals.append(position)
            
    bb_df['Buy_Signal'] = signals
    prev_signals = bb_df['Buy_Signal'].shift(1).fillna(False)
    
    entry_cost = np.where((bb_df['Buy_Signal'] == True) & (prev_signals == False), cost_rate, 0.0)
    exit_cost = np.where((bb_df['Buy_Signal'] == False) & (prev_signals == True), cost_rate, 0.0)
    total_cost = entry_cost + exit_cost
    
    # 배당 재투자 수익률 계산
    if use_drip and '배당금' in bb_df.columns:
        div_yield = bb_df['배당금'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])
        strategy_div_yield = np.where(bb_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    bb_df['Strategy_Return'] = np.where(
        bb_df['Buy_Signal'],
        (bb_df['종가'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])) - total_cost + strategy_div_yield,
        1.0 - total_cost
    )
    bb_df['Strategy_Return'] = bb_df['Strategy_Return'].fillna(1.0)
    
    hold_returns = (bb_df['종가'] / bb_df['종가'].shift(1).fillna(bb_df['종가'])) + div_yield
    hold_returns_array = hold_returns.fillna(1.0).values
    if len(hold_returns_array) > 0:
        hold_returns_array[0] = hold_returns_array[0] - cost_rate
    bb_df['Hold_Return'] = hold_returns_array
    
    bb_df['Strategy_Cum_Return'] = (bb_df['Strategy_Return'].cumprod() - 1) * 100
    bb_df['Hold_Cum_Return'] = (bb_df['Hold_Return'].cumprod() - 1) * 100
    bb_df['Strategy_Balance'] = initial_budget * bb_df['Strategy_Return'].cumprod()
    bb_df['Hold_Balance'] = initial_budget * bb_df['Hold_Return'].cumprod()
    
    bb_df['Daily_Return_Pct'] = (bb_df['Strategy_Return'] - 1) * 100
    return bb_df

def calculate_bb_monthly_stats(bb_df):
    bb_df['YearMonth'] = bb_df.index.strftime('%Y-%m')
    bb_df['Buy_Count'] = np.where(bb_df['Buy_Signal'], 1, 0)
    summary = bb_df.groupby('YearMonth').agg({
        'Buy_Count': 'sum',
        'Strategy_Return': 'prod',
        'Hold_Return': 'prod'
    }).reset_index()
    summary['Strategy_Return'] = (summary['Strategy_Return'] - 1) * 100
    summary['Hold_Return'] = (summary['Hold_Return'] - 1) * 100
    summary.columns = ['년-월', '매수 보유 일수 (일)', '전략 수익률 (%)', '단순 보유 수익률 (%)']
    return summary


def finalize_signal_backtest(signal_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    """Boolean Buy_Signal 컬럼을 가진 전략 DataFrame에 수익률/잔고 컬럼을 붙입니다."""
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    out = signal_df.copy()
    out['Buy_Signal'] = out['Buy_Signal'].fillna(False).astype(bool)
    prev_signals = out['Buy_Signal'].shift(1).fillna(False)
    entry_cost = np.where(out['Buy_Signal'] & ~prev_signals, cost_rate, 0.0)
    exit_cost = np.where(~out['Buy_Signal'] & prev_signals, cost_rate, 0.0)
    total_cost = entry_cost + exit_cost

    if use_drip and '배당금' in out.columns:
        div_yield = out['배당금'] / out['종가'].shift(1).fillna(out['종가'])
        strategy_div_yield = np.where(out['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0

    daily_price_return = out['종가'] / out['종가'].shift(1).fillna(out['종가'])
    out['Strategy_Return'] = np.where(
        out['Buy_Signal'],
        daily_price_return - total_cost + strategy_div_yield,
        1.0 - total_cost,
    )
    out['Strategy_Return'] = out['Strategy_Return'].fillna(1.0)

    hold_returns = (daily_price_return + div_yield).fillna(1.0).values
    if len(hold_returns) > 0:
        hold_returns[0] = hold_returns[0] - cost_rate
    out['Hold_Return'] = hold_returns
    out['Strategy_Cum_Return'] = (out['Strategy_Return'].cumprod() - 1) * 100
    out['Hold_Cum_Return'] = (out['Hold_Return'].cumprod() - 1) * 100
    out['Strategy_Balance'] = initial_budget * out['Strategy_Return'].cumprod()
    out['Hold_Balance'] = initial_budget * out['Hold_Return'].cumprod()
    out['Daily_Return_Pct'] = (out['Strategy_Return'] - 1) * 100
    return out


def calculate_signal_monthly_stats(strategy_df):
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
    return summary


def run_stochastic_backtest(df, k_period, d_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    stoch_df = df.copy()
    low_min = stoch_df['저가'].rolling(k_period).min()
    high_max = stoch_df['고가'].rolling(k_period).max()
    stoch_df['%K'] = ((stoch_df['종가'] - low_min) / (high_max - low_min)) * 100
    stoch_df['%D'] = stoch_df['%K'].rolling(d_period).mean()
    stoch_df['Buy_Signal'] = stoch_df['%K'] > stoch_df['%D']
    return finalize_signal_backtest(stoch_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip)


def run_ichimoku_backtest(df, conversion_period, base_period, span_b_period, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    ichi_df = df.copy()
    conv_high = ichi_df['고가'].rolling(conversion_period).max()
    conv_low = ichi_df['저가'].rolling(conversion_period).min()
    base_high = ichi_df['고가'].rolling(base_period).max()
    base_low = ichi_df['저가'].rolling(base_period).min()
    span_b_high = ichi_df['고가'].rolling(span_b_period).max()
    span_b_low = ichi_df['저가'].rolling(span_b_period).min()
    ichi_df['Conversion'] = (conv_high + conv_low) / 2
    ichi_df['Base'] = (base_high + base_low) / 2
    ichi_df['Span_A'] = ((ichi_df['Conversion'] + ichi_df['Base']) / 2).shift(base_period)
    ichi_df['Span_B'] = ((span_b_high + span_b_low) / 2).shift(base_period)
    cloud_top = pd.concat([ichi_df['Span_A'], ichi_df['Span_B']], axis=1).max(axis=1)
    ichi_df['Buy_Signal'] = (ichi_df['종가'] > cloud_top) & (ichi_df['Conversion'] > ichi_df['Base'])
    return finalize_signal_backtest(ichi_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip)


def run_adx_dmi_backtest(df, period, adx_threshold, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    adx_df = df.copy()
    high = adx_df['고가']
    low = adx_df['저가']
    close = adx_df['종가']
    plus_dm = (high.diff()).where((high.diff() > -low.diff()) & (high.diff() > 0), 0.0)
    minus_dm = (-low.diff()).where((-low.diff() > high.diff()) & (-low.diff() > 0), 0.0)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    adx_df['+DI'] = 100 * plus_dm.rolling(period).mean() / atr
    adx_df['-DI'] = 100 * minus_dm.rolling(period).mean() / atr
    dx = ((adx_df['+DI'] - adx_df['-DI']).abs() / (adx_df['+DI'] + adx_df['-DI'])) * 100
    adx_df['ADX'] = dx.rolling(period).mean()
    adx_df['Buy_Signal'] = (adx_df['+DI'] > adx_df['-DI']) & (adx_df['ADX'] >= adx_threshold)
    return finalize_signal_backtest(adx_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip)


def run_envelope_backtest(df, period, envelope_pct, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):
    env_df = df.copy()
    env_df['MA'] = env_df['종가'].rolling(period).mean()
    env_df['Upper_Envelope'] = env_df['MA'] * (1 + envelope_pct / 100)
    env_df['Lower_Envelope'] = env_df['MA'] * (1 - envelope_pct / 100)
    signals = []
    position = False
    was_below_lower = False
    for close, lower, ma in zip(env_df['종가'], env_df['Lower_Envelope'], env_df['MA']):
        if pd.isna(lower) or pd.isna(ma):
            signals.append(False)
        elif not position and close < lower:
            was_below_lower = True
            signals.append(False)
        elif not position and was_below_lower and close > lower:
            position = True
            was_below_lower = False
            signals.append(True)
        elif position and close >= ma:
            position = False
            signals.append(False)
        else:
            signals.append(position)
    env_df['Buy_Signal'] = signals
    return finalize_signal_backtest(env_df, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip)


def run_static_allocation_backtest(asset_data, weights, initial_budget, fee_rate_pct, slippage_rate_pct):
    combined = pd.DataFrame({ticker: df['종가'] for ticker, df in asset_data.items()}).sort_index().ffill().dropna()
    if combined.empty:
        return combined
    returns = combined.pct_change().fillna(0.0) + 1.0
    weight_series = pd.Series(weights).reindex(combined.columns).fillna(0.0)
    weight_series = weight_series / weight_series.sum()
    rebalance_dates = combined.groupby(combined.index.to_period('M')).head(1).index
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    turnover_cost = pd.Series(0.0, index=combined.index)
    turnover_cost.loc[rebalance_dates] = cost_rate
    strategy_return = (returns * weight_series).sum(axis=1) - turnover_cost
    strategy_return = strategy_return.clip(lower=0.0)
    hold_return = returns.iloc[:, 0]

    out = pd.DataFrame(index=combined.index)
    out['종가'] = combined.iloc[:, 0]
    out['Strategy_Return'] = strategy_return
    out['Hold_Return'] = hold_return
    out['Strategy_Cum_Return'] = (out['Strategy_Return'].cumprod() - 1) * 100
    out['Hold_Cum_Return'] = (out['Hold_Return'].cumprod() - 1) * 100
    out['Strategy_Balance'] = initial_budget * out['Strategy_Return'].cumprod()
    out['Hold_Balance'] = initial_budget * out['Hold_Return'].cumprod()
    out['Daily_Return_Pct'] = (out['Strategy_Return'] - 1) * 100
    out['Buy_Signal'] = out.index.isin(rebalance_dates)
    out['Selected_Asset'] = " / ".join([f"{ticker} {weight_series[ticker]*100:.1f}%" for ticker in combined.columns])
    return out

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="주식 투자 전략 백테스트 종합 비교 대시보드", layout="wide")

# 프리미엄 다크/그레이 톤 스타일링을 위한 마크다운 CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .staleElement,
    [data-testid="staleElement"],
    [data-stale="true"] {
        opacity: 1 !important;
        filter: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 주식 투자 전략 시뮬레이터 및 백테스트 대시보드")
st.write("다양한 퀀트 전략 및 머신러닝 모델의 성과를 분석하는 인터랙티브 대시보드입니다.")

# 세션 상태 초기화 및 관리
if 'run_backtest' not in st.session_state:
    st.session_state['run_backtest'] = False
if 'scanner_results' not in st.session_state:
    st.session_state['scanner_results'] = None
if 'scanner_keyword' not in st.session_state:
    st.session_state['scanner_keyword'] = ""
if 'target_ticker' not in st.session_state:
    st.session_state['target_ticker'] = ""

# 🔍 지수/ETF 리스트 결과 표시 영역 (오른쪽 메인 화면)
if st.session_state['scanner_results'] is not None:
    with st.expander(f"🔍 {st.session_state['scanner_keyword']} 결과 ({len(st.session_state['scanner_results'])}개)", expanded=True):
        df_results = pd.DataFrame(st.session_state['scanner_results'])

        def apply_scanner_ticker(selected_ticker):
            st.session_state["target_ticker"] = selected_ticker
            st.session_state["run_backtest"] = False
            st.session_state['scanner_results'] = None
            st.session_state['scanner_keyword'] = ""
            st.rerun()

        event = st.dataframe(
            df_results,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="scanner_results_table",
        )
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            if "티커" in df_results.columns:
                selected_ticker = str(df_results.iloc[selected_idx]["티커"])
                if st.session_state.get("target_ticker") != selected_ticker:
                    apply_scanner_ticker(selected_ticker)

        if "티커" in df_results.columns:
            ticker_options = [str(ticker) for ticker in df_results["티커"].dropna().tolist()]
            selected_label = st.selectbox(
                "티커 선택",
                options=ticker_options,
                format_func=lambda ticker: f"{ticker} - {df_results.loc[df_results['티커'].astype(str) == ticker, '종목명'].iloc[0]}" if "종목명" in df_results.columns else ticker,
                key="scanner_ticker_selectbox",
            )
            if st.button("선택한 티커 적용", key="apply_scanner_ticker", use_container_width=True):
                apply_scanner_ticker(selected_label)

        c1, c2 = st.columns([6, 1])
        c1.caption("※ 표 행 선택이 안 될 때는 위의 티커 선택 상자에서 종목을 고른 뒤 적용하세요.")
        if c2.button("결과 닫기", key="close_scanner_results", use_container_width=True):
            st.session_state['scanner_results'] = None
            st.session_state['scanner_keyword'] = ""
            st.rerun()

# 사이드바 설정
# 🔍 지수/ETF 리스트 (사이드바 맨 위 배치)
with st.sidebar.expander("🔍 지수/ETF 카테고리 검색", expanded=False):
    with st.form(key="scanner_form_sb", clear_on_submit=False):
        etf_category = st.selectbox("분류 선택", options=list(INDEX_ETF_CATALOG.keys()))
        submit_btn = st.form_submit_button("목록 보기", use_container_width=True)
    
    if submit_btn:
        found_stocks = INDEX_ETF_CATALOG.get(etf_category, [])
        if found_stocks:
            st.sidebar.success("지수/ETF 리스트 조회 완료! 우측 화면을 확인하세요.")
            st.session_state['scanner_results'] = found_stocks
            st.session_state['scanner_keyword'] = etf_category
            st.rerun()
        else:
            st.sidebar.warning("선택한 분류의 지수/ETF를 찾지 못했습니다.")
            st.session_state['scanner_results'] = None
            st.session_state['scanner_keyword'] = ""
            st.rerun()

# 🔍 공통 종목 코드 직접 입력
ticker_input = st.sidebar.text_input("🔍 종목 코드/종목명 직접 입력 (예: SPY, 삼성전자, 005930)", key="target_ticker")
ticker_matches = search_local_tickers(ticker_input)
if len(ticker_matches) > 1:
    selected_match_label = st.sidebar.selectbox(
        "검색된 종목 중 선택",
        options=[f"{match['name']} ({match['ticker']})" for match in ticker_matches],
        index=0,
    )
    selected_match_index = [f"{match['name']} ({match['ticker']})" for match in ticker_matches].index(selected_match_label)
    ticker_code = ticker_matches[selected_match_index]["ticker"]
elif len(ticker_matches) == 1:
    ticker_code = ticker_matches[0]["ticker"]
else:
    ticker_code = resolve_ticker_input(ticker_input)
ticker_symbol = ticker_code.strip().upper()
ticker_name = get_ticker_name(ticker_code)
is_known_ticker = ticker_name != UNKNOWN_TICKER_NAME
if is_known_ticker:
    if len(ticker_matches) > 1:
        st.sidebar.info(f"검색어: **{ticker_input.strip()}** → 선택된 종목: **{ticker_name}** ({ticker_symbol})")
    elif ticker_input.strip() != ticker_code:
        st.sidebar.info(f"검색어: **{ticker_input.strip()}** → 선택된 종목: **{ticker_name}** ({ticker_symbol})")
    else:
        st.sidebar.info(f"선택된 종목: **{ticker_name}** ({ticker_symbol})")
else:
    if not ticker_input.strip():
        st.sidebar.info("💡 분석할 종목 코드 또는 종목명을 위에 입력해 주세요.")
    else:
        unknown_label = ticker_input.strip()
        hint = INVALID_TICKER_HINTS.get(ticker_symbol, "")
        st.sidebar.warning(f"알 수 없는 종목 코드 또는 종목명입니다: **{unknown_label}**")
        if hint:
            st.sidebar.info(hint)

st.sidebar.header("⚙️ 전략 및 파라미터 설정")

# 1. 라디오 버튼을 사용하여 전략 및 통합 모드 선택 (3개 옵션 제공)
strategy_choice = st.sidebar.radio(
    "💡 분석할 전략 선택",
    options=[
        "머신러닝 롤링 예측 전략",
        "변동성 돌파 전략 (Larry Williams)",
        "두 전략 통합 비교",
        "듀얼 모멘텀 전략",
        "이동평균선 골든크로스 전략",
        "RSI 과매도 반등 전략",
        "볼린저 밴드 반등 전략",
        "MACD 추세 전략",
        "스토캐스틱 오실레이터 전략",
        "일목균형표 전환/기준선 전략",
        "ADX/DMI 추세 전략",
        "엔벨로프 반등 전략",
        "영구 포트폴리오 전략",
        "올웨더 포트폴리오 전략"
    ]
)

# 🚀 백테스트 실행 버튼은 날짜 입력 바로 위에 고정
run_button_clicked = st.sidebar.button("🚀 백테스트 실행하기", use_container_width=True)
if run_button_clicked:
    st.session_state['run_backtest'] = True

# 3. 공통 기간 설정 (종료 날짜 기본값을 실행 당일 오늘 날짜로 동적 자동 입력)
start_date = st.sidebar.text_input("시작 날짜 (YYYYMMDD)", "20240101")
today_str = datetime.today().strftime('%Y%m%d')
end_date = st.sidebar.text_input("종료 날짜 (YYYYMMDD)", today_str)

# 4. 실전 투자 조건 설정 (사용자가 쉼표 없이 숫자만 편리하게 타이핑하여 입력하도록 원복)
st.sidebar.subheader("💸 실전 투자 조건 (거래비용)")
initial_budget = st.sidebar.number_input("💵 초기 투자 원금 (원)", min_value=100000, value=10000000, step=1000000, format="%d")

fee_rate = st.sidebar.number_input("💸 거래 수수료율 (편도, %)", min_value=0.0, max_value=1.0, value=0.15, step=0.01, format="%.3f")
slippage_rate = st.sidebar.number_input("📉 슬리피지율 (편도, %)", min_value=0.0, max_value=1.0, value=0.10, step=0.01, format="%.2f")

# [LOG: 20260604_0904]
# 배당금 재투자 (DRIP) 여부 설정
use_drip = st.sidebar.checkbox("🔄 배당금 재투자 (DRIP) 반영", value=False)

# 5. 전략별 개별 설정
st.sidebar.subheader("🎯 전략 파라미터")
dm_lookback_days = 252
dm_defense_ticker = "IEF"
dm_defensive_mode = "방어자산"
if strategy_choice == "머신러닝 롤링 예측 전략":
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    window_size = 90
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "듀얼 모멘텀 전략":
    dm_default_option = "채권 (안전자산/피신처) | IEF - 중기 미국채 (7-10년)"
    dm_asset_option = st.sidebar.selectbox(
        "비교/방어 자산 선택",
        options=DUAL_MOMENTUM_ASSET_OPTIONS,
        index=DUAL_MOMENTUM_ASSET_OPTIONS.index(dm_default_option),
        help="현재 종목 입력창의 티커가 공격 자산이고, 여기서 고른 자산과 월별 모멘텀을 비교합니다.",
    )
    if dm_asset_option == "직접 입력":
        dm_defense_ticker = st.sidebar.text_input("비교/방어 자산 티커 직접 입력", "IEF")
    else:
        dm_defense_ticker = DUAL_MOMENTUM_TICKER_BY_OPTION[dm_asset_option]
        st.sidebar.caption(f"선택된 비교 자산: {dm_defense_ticker}")
    dm_lookback_months = st.sidebar.selectbox("모멘텀 비교 기간", options=[3, 6, 12], index=2)
    dm_lookback_days = dm_lookback_months * 21
    dm_defensive_mode = st.sidebar.radio("둘 다 약할 때", options=["방어자산", "현금"], horizontal=True)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "이동평균선 골든크로스 전략":
    ma_short = st.sidebar.slider("단기 이동평균선 (일)", min_value=5, max_value=50, value=20, step=5)
    ma_long = st.sidebar.slider("장기 이동평균선 (일)", min_value=20, max_value=200, value=60, step=10)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
elif strategy_choice == "RSI 과매도 반등 전략":
    rsi_period = st.sidebar.slider("RSI 계산 기간 (일)", min_value=5, max_value=30, value=14, step=1)
    buy_rsi = st.sidebar.slider("매수 기준 RSI (이하)", min_value=10, max_value=50, value=30, step=5)
    sell_rsi = st.sidebar.slider("매도 기준 RSI (이상)", min_value=50, max_value=90, value=70, step=5)
    window_size = 90
    K = 0.5
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "볼린저 밴드 반등 전략":
    bb_period = st.sidebar.slider("이동평균 기간 (일)", min_value=5, max_value=50, value=20, step=5)
    bb_std = st.sidebar.slider("표준편차 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    ma_short, ma_long = 20, 60
elif strategy_choice == "MACD 추세 전략":
    macd_fast = st.sidebar.slider("단기 EMA 기간 (일)", min_value=5, max_value=30, value=12, step=1)
    macd_slow = st.sidebar.slider("장기 EMA 기간 (일)", min_value=20, max_value=60, value=26, step=1)
    macd_signal = st.sidebar.slider("시그널 EMA 기간 (일)", min_value=3, max_value=20, value=9, step=1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "스토캐스틱 오실레이터 전략":
    stoch_k = st.sidebar.slider("%K 기간", min_value=5, max_value=30, value=14, step=1)
    stoch_d = st.sidebar.slider("%D 기간", min_value=2, max_value=10, value=3, step=1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "일목균형표 전환/기준선 전략":
    ichi_conversion = st.sidebar.slider("전환선 기간", min_value=5, max_value=20, value=9, step=1)
    ichi_base = st.sidebar.slider("기준선 기간", min_value=20, max_value=40, value=26, step=1)
    ichi_span_b = st.sidebar.slider("선행스팬B 기간", min_value=40, max_value=80, value=52, step=1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "ADX/DMI 추세 전략":
    adx_period = st.sidebar.slider("ADX/DMI 기간", min_value=7, max_value=30, value=14, step=1)
    adx_threshold = st.sidebar.slider("ADX 기준값", min_value=10, max_value=50, value=25, step=1)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "엔벨로프 반등 전략":
    envelope_period = st.sidebar.slider("엔벨로프 이동평균 기간", min_value=5, max_value=60, value=20, step=5)
    envelope_pct = st.sidebar.slider("엔벨로프 폭 (%)", min_value=1.0, max_value=20.0, value=10.0, step=0.5)
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "영구 포트폴리오 전략":
    permanent_assets = {"SPY": 0.25, "TLT": 0.25, "GLD": 0.25, "BIL": 0.25}
    st.sidebar.caption("기본 구성: SPY 25%, TLT 25%, GLD 25%, BIL 25%")
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
elif strategy_choice == "올웨더 포트폴리오 전략":
    allweather_assets = {"SPY": 0.30, "TLT": 0.40, "IEF": 0.15, "DBC": 0.075, "GLD": 0.075}
    st.sidebar.caption("기본 구성: SPY 30%, TLT 40%, IEF 15%, DBC 7.5%, GLD 7.5%")
    window_size = 90
    K = 0.5
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60
else:
    # 통합 비교 모드 시 두 설정 모두 표시
    window_size = st.sidebar.slider("학습 윈도우 크기 (영업일 기준)", min_value=30, max_value=120, value=90)
    K = st.sidebar.slider("변동성 돌파 계수 (K)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
    rsi_period, buy_rsi, sell_rsi = 14, 30, 70
    bb_period, bb_std = 20, 2.0
    ma_short, ma_long = 20, 60

# --- 세션 상태 초기화 및 관리 ---
if 'stock_data' not in st.session_state:
    st.session_state['stock_data'] = pd.DataFrame()
if 'loaded_ticker' not in st.session_state:
    st.session_state['loaded_ticker'] = ""
if 'loaded_start' not in st.session_state:
    st.session_state['loaded_start'] = ""
if 'loaded_end' not in st.session_state:
    st.session_state['loaded_end'] = ""

# 입력된 종목코드나 기간이 이미 세션에 로드된 것과 일치하는지 판별
is_data_cached = (
    not st.session_state['stock_data'].empty and
    st.session_state['loaded_ticker'] == ticker_code.strip() and
    st.session_state['loaded_start'] == start_date and
    st.session_state['loaded_end'] == end_date
)
# 백테스트용 주가 데이터는 실행 버튼을 누른 경우에만 로드합니다.
if not is_known_ticker:
    st.session_state['stock_data'] = pd.DataFrame()
    st.session_state['loaded_ticker'] = ""
    st.session_state['loaded_start'] = ""
    st.session_state['loaded_end'] = ""
    st.session_state['run_backtest'] = False
elif not is_data_cached and st.session_state.get('run_backtest', False):
    with st.spinner(f"📡 {ticker_name} ({ticker_symbol}) 주식 데이터를 불러오는 중..."):
        df = load_data(start_date, end_date, ticker_code)
        if not df.empty:
            st.session_state['stock_data'] = df
            st.session_state['loaded_ticker'] = ticker_code.strip()
            st.session_state['loaded_start'] = start_date
            st.session_state['loaded_end'] = end_date
        else:
            st.session_state['stock_data'] = pd.DataFrame()
elif not is_data_cached:
    st.session_state['stock_data'] = pd.DataFrame()
    st.session_state['loaded_ticker'] = ""
    st.session_state['loaded_start'] = ""
    st.session_state['loaded_end'] = ""
    st.session_state['run_backtest'] = False

# [LOG: 20260606_2136] 전략 설명 추가
STRATEGY_DESCRIPTIONS = {
    "머신러닝 롤링 예측 전략": """
    **🤖 머신러닝 롤링 예측 전략**
    - **원리**: 매일 과거 N영업일(학습 윈도우 크기)의 시가, 저가, 종가, 거래량 데이터를 학습하여 다음 날 종가를 랜덤포레스트 모델로 예측합니다.
    - **매매 규칙**: 내일 주가가 오늘보다 상승할 것으로 예측되면 오늘 종가에 매수하고, 하락할 것으로 예측되면 전량 매도하여 현금화합니다.
    - **특징**: 시장의 최근 패턴을 실시간(롤링)으로 머신러닝 모델이 자가학습하여 추세를 유연하게 추종합니다.
    """,
    "변동성 돌파 전략 (Larry Williams)": """
    **⚡ 변동성 돌파 전략 (Larry Williams)**
    - **원리**: 전일 고가와 저가의 폭(변동폭)에 돌파 계수 K(기본 0.5)를 곱한 값을 당일 시가에 더하여 '목표 매수 가격'을 설정합니다.
    - **매매 규칙**: 장중에 주가가 목표 가격을 돌파(터치)하는 즉시 매수하며, 당일 종가에 무조건 전량 매도하여 오버나이트(밤사이 보유) 위험을 회피합니다.
    - **특징**: 추세가 아주 강한 날만 당일 단타로 진입하므로 하락장에서 계좌를 매우 안전하게 방어합니다.
    """,
    "두 전략 통합 비교": """
    **⚖️ 두 전략 통합 비교**
    - **내용**: 본 대시보드의 메인 테마인 **'머신러닝 롤링 예측 전략'**과 **'변동성 돌파 전략'**의 수익률 추이, 자산 잔고, 거래 지표 등을 한 화면에 나란히 비교합니다.
    - **특징**: 어떤 시장 국면에서 어떤 전략이 상대적으로 더 우수한 성과를 내는지 한눈에 비교 분석할 수 있습니다.
    """,
    "듀얼 모멘텀 전략": """
    **🧭 듀얼 모멘텀 전략**
    - **원리**: 현재 입력한 공격 자산과 선택한 비교/방어 자산의 최근 3/6/12개월 수익률을 월말마다 비교합니다.
    - **매매 규칙**: 공격 자산 모멘텀이 더 강하고 양수이면 공격 자산을 보유하고, 그렇지 않으면 방어 자산 또는 현금으로 이동합니다.
    - **특징**: 상승장에서는 강한 자산을 따라가고, 약세장에서는 국채나 현금으로 대피하는 자산 전환 전략입니다.
    """,
    "이동평균선 골든크로스 전략": """
    **📈 이동평균선 골든크로스 전략**
    - **원리**: 주가의 단기 이동평균선(예: 20일)과 장기 이동평균선(예: 60일)의 교차(Cross)를 활용하여 대세 추세를 추종합니다.
    - **매매 규칙**: 단기 이평선이 장기 이평선을 위로 뚫고 올라갈 때(골든크로스) 매수하여 보유하고, 아래로 뚫고 내려갈 때(데드크로스) 매도하여 현금화합니다.
    - **특징**: 장기적인 상승/하락 추세를 포착하는 데 가장 널리 쓰이는 클래식한 추세 추종 전략입니다.
    """,
    "RSI 과매도 반등 전략": """
    **🔄 RSI 과매도 반등 전략**
    - **원리**: 가격의 상승 압력과 하락 압력 간의 상대적인 강도를 백분율로 나타낸 RSI(Relative Strength Index) 지표를 활용합니다.
    - **매매 규칙**: RSI 지표가 과매도 기준선(예: 30) 이하로 떨어졌다가 다시 반등하기 시작할 때 매수하고, 과열 기준선(예: 70) 이상으로 올라가면 매도하여 이익을 실현합니다.
    - **특징**: 주가가 박스권 횡보를 하거나 단기 과매도로 인해 일시적으로 급락했을 때 기술적 반등을 노리는 역추세 전략입니다.
    """,
    "볼린저 밴드 반등 전략": """
    **🔘 볼린저 밴드 반등 전략**
    - **원리**: 이동평균선(기본 20일)을 중심으로 주가 변동성의 표준편차 범위를 밴드로 그려, 주가가 밴드 범위 안에서 움직일 확률이 높다는 특성을 활용합니다.
    - **매매 규칙**: 주가가 밴드의 하단선 이하로 떨어져 과도하게 저평가되었을 때 매수하고, 상단선 부근에 도달하여 저항을 받을 때 매도합니다.
    - **특징**: 전형적인 박스권 시장에서 높은 승률을 보이며, 과도한 이격을 원래 평균값으로 회복하는 성질(평균 회귀)을 이용합니다.
    """,
    "MACD 추세 전략": """
    **📊 MACD 추세 전략**
    - **원리**: 단기 지수이동평균선(EMA)과 장기 지수이동평균선의 차이를 나타내는 MACD선과, 이를 다시 지수이동평균한 Signal선의 골든/데드크로스를 활용합니다.
    - **매매 규칙**: MACD선이 Signal선을 상향 돌파(골든크로스)할 때 매수하여 보유하고, 하향 돌파(데드크로스)할 때 매도하여 빠져나옵니다.
    - **특징**: 일반 이동평균선 크로스보다 가격 변화에 더욱 민감하고 빠르게 대응할 수 있는 대중적인 추세 추종 보조지표 전략입니다.
    """,
    "스토캐스틱 오실레이터 전략": """
    **📉 스토캐스틱 오실레이터 전략**
    - **원리**: 최근 고가/저가 범위에서 현재 종가가 어디에 있는지 %K/%D로 측정합니다.
    - **매매 규칙**: %K가 %D 위에 있으면 보유하고, 아래로 내려가면 현금화합니다.
    """,
    "일목균형표 전환/기준선 전략": """
    **☁️ 일목균형표 전환/기준선 전략**
    - **원리**: 전환선, 기준선, 구름대를 이용해 추세 방향을 판단합니다.
    - **매매 규칙**: 종가가 구름대 위이고 전환선이 기준선보다 높으면 보유합니다.
    """,
    "ADX/DMI 추세 전략": """
    **📐 ADX/DMI 추세 전략**
    - **원리**: +DI/-DI로 방향을 보고 ADX로 추세 강도를 확인합니다.
    - **매매 규칙**: +DI가 -DI보다 높고 ADX가 기준값 이상이면 보유합니다.
    """,
    "엔벨로프 반등 전략": """
    **📎 엔벨로프 반등 전략**
    - **원리**: 이동평균선 상하단 밴드에서 과매도 반등을 포착합니다.
    - **매매 규칙**: 하단 밴드 위로 회복하면 매수하고 중심선 회복 시 매도합니다.
    """,
    "영구 포트폴리오 전략": """
    **🧱 영구 포트폴리오 전략**
    - **원리**: 주식, 장기채, 금, 현금을 각각 25%로 보유하는 정적 자산배분 전략입니다.
    - **매매 규칙**: 월초 목표 비중으로 리밸런싱합니다.
    """,
    "올웨더 포트폴리오 전략": """
    **🌦️ 올웨더 포트폴리오 전략**
    - **원리**: 주식 30%, 장기채 40%, 중기채 15%, 원자재 7.5%, 금 7.5%로 분산합니다.
    - **매매 규칙**: 월초 목표 비중으로 리밸런싱합니다.
    """
}

desc_content = STRATEGY_DESCRIPTIONS.get(strategy_choice, "")
if desc_content:
    with st.expander("전략 설명 보기", expanded=False):
        st.info(desc_content)

if ticker_input.strip() and is_known_ticker and not st.session_state.get('run_backtest', False):
    render_financial_data_section(ticker_code, ticker_name)
    st.divider()

# [LOG: 20260604_1502]
# 백테스트 실행 및 예외 제어문 최적화
df = st.session_state['stock_data']

if not ticker_input.strip():
    st.info("👈 왼쪽 사이드바에서 [종목 코드/종목명]을 입력한 뒤 [백테스트 실행하기] 버튼을 눌러주세요.")
elif not is_known_ticker:
    hint = INVALID_TICKER_HINTS.get(ticker_symbol, "")
    err_msg = f"❌ 알 수 없는 종목 코드 또는 종목명입니다: **{ticker_input.strip()}**"
    if hint:
        err_msg += f"\n\n💡 도움말: {hint}"
    st.error(err_msg)
elif df.empty:
    if st.session_state.get('run_backtest', False):
        st.error("❌ 주식 데이터를 불러오지 못했습니다. 올바른 종목 코드 및 백테스트 기간을 다시 확인해 주세요.")
    else:
        st.info("👈 왼쪽 사이드바에서 조건을 입력하고 [백테스트 실행하기] 버튼을 눌러주세요.")
else:
    if st.session_state.get('run_backtest', False):
        run_status_area = st.container()
        run_status_message = run_status_area.empty()
        progress_area = run_status_area.container()
        run_status_message.info(f"⏳ 백테스트 실행 중... {ticker_name} ({ticker_symbol}) / {strategy_choice}")

        # 1. 1차 검증
        if strategy_choice in ["머신러닝 롤링 예측 전략", "두 전략 통합 비교"] and len(df) <= window_size:
            st.error(f"데이터의 총 크기({len(df)}일)가 학습 윈도우 크기({window_size}일)보다 작습니다. 기간을 늘려주세요.")
        elif strategy_choice == "듀얼 모멘텀 전략" and len(df) <= dm_lookback_days:
            st.error(f"데이터의 총 크기({len(df)}일)가 모멘텀 비교 기간({dm_lookback_days}영업일)보다 작습니다. 기간을 늘려주세요.")
        else:
            # --- 백테스트 연산 수행 ---
            
            # 머신러닝 모드 연산
            if strategy_choice == "머신러닝 롤링 예측 전략":
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                actual_close = df['종가'].loc[pred_series.index]
                ml_df = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate, use_drip)
                
                # 평가 지표
                mae = (actual_close - pred_series).abs().mean()
                mape = ((actual_close - pred_series).abs() / actual_close).mean() * 100
                strategy_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                total_days = len(pred_series)
                
            # 변동성 돌파 모드 연산
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                vbt_df = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = vbt_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = vbt_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(vbt_df['Buy_Signal'])
                total_days = len(vbt_df)
                
            # 이동평균선 골든크로스 연산
            elif strategy_choice == "이동평균선 골든크로스 전략":
                ma_df = run_ma_cross_backtest(df, ma_short, ma_long, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = ma_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ma_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = ma_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ma_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(ma_df['Buy_Signal'] & (~ma_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(ma_df)

            # RSI 과매도 반등 연산
            elif strategy_choice == "RSI 과매도 반등 전략":
                rsi_df = run_rsi_backtest(df, rsi_period, buy_rsi, sell_rsi, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = rsi_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = rsi_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = rsi_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = rsi_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(rsi_df['Buy_Signal'] & (~rsi_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(rsi_df)

            # 볼린저 밴드 반등 연산
            elif strategy_choice == "볼린저 밴드 반등 전략":
                bb_df = run_bollinger_backtest(df, bb_period, bb_std, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = bb_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = bb_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = bb_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = bb_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(bb_df['Buy_Signal'] & (~bb_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(bb_df)

            # 듀얼 모멘텀 연산
            elif strategy_choice == "듀얼 모멘텀 전략":
                defense_ticker_code = resolve_ticker_input(dm_defense_ticker)
                defense_ticker_name = get_ticker_name(defense_ticker_code)
                with st.spinner(f"📡 비교/방어 자산 {defense_ticker_name} ({defense_ticker_code}) 데이터를 불러오는 중..."):
                    defense_df = load_data(start_date, end_date, defense_ticker_code)

                if defense_ticker_name == UNKNOWN_TICKER_NAME or defense_df.empty:
                    st.error("❌ 비교/방어 자산 데이터를 불러오지 못했습니다. 티커를 다시 확인해 주세요.")
                    st.stop()

                dm_df = run_dual_momentum_backtest(
                    df,
                    defense_df,
                    ticker_symbol,
                    defense_ticker_code.strip().upper(),
                    dm_lookback_days,
                    initial_budget,
                    fee_rate,
                    slippage_rate,
                    dm_defensive_mode,
                    use_drip,
                )
                if dm_df.empty:
                    st.error("❌ 공격 자산과 비교/방어 자산의 공통 거래일 데이터가 부족합니다.")
                    st.stop()

                strategy_final_return = dm_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = dm_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = dm_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = dm_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(dm_df['Position'] != dm_df['Position'].shift(1).fillna("CASH"))
                total_days = len(dm_df)

            # MACD 추세 연산
            elif strategy_choice == "MACD 추세 전략":
                macd_df = run_macd_backtest(df, macd_fast, macd_slow, macd_signal, initial_budget, fee_rate, slippage_rate, use_drip)
                strategy_final_return = macd_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = macd_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = macd_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = macd_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(macd_df['Buy_Signal'] & (~macd_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(macd_df)

            elif strategy_choice == "스토캐스틱 오실레이터 전략":
                generic_df = run_stochastic_backtest(df, stoch_k, stoch_d, initial_budget, fee_rate, slippage_rate, use_drip)
                generic_label = "📉 스토캐스틱"
                strategy_final_return = generic_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = generic_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = generic_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(generic_df['Buy_Signal'] & (~generic_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(generic_df)

            elif strategy_choice == "일목균형표 전환/기준선 전략":
                generic_df = run_ichimoku_backtest(df, ichi_conversion, ichi_base, ichi_span_b, initial_budget, fee_rate, slippage_rate, use_drip)
                generic_label = "☁️ 일목균형표"
                strategy_final_return = generic_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = generic_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = generic_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(generic_df['Buy_Signal'] & (~generic_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(generic_df)

            elif strategy_choice == "ADX/DMI 추세 전략":
                generic_df = run_adx_dmi_backtest(df, adx_period, adx_threshold, initial_budget, fee_rate, slippage_rate, use_drip)
                generic_label = "📐 ADX/DMI"
                strategy_final_return = generic_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = generic_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = generic_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(generic_df['Buy_Signal'] & (~generic_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(generic_df)

            elif strategy_choice == "엔벨로프 반등 전략":
                generic_df = run_envelope_backtest(df, envelope_period, envelope_pct, initial_budget, fee_rate, slippage_rate, use_drip)
                generic_label = "📎 엔벨로프"
                strategy_final_return = generic_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = generic_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = generic_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(generic_df['Buy_Signal'] & (~generic_df['Buy_Signal'].shift(1).fillna(False)))
                total_days = len(generic_df)

            elif strategy_choice in ["영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                portfolio_assets = permanent_assets if strategy_choice == "영구 포트폴리오 전략" else allweather_assets
                asset_data = {}
                with st.spinner("📡 포트폴리오 구성 ETF 데이터를 불러오는 중..."):
                    for asset_ticker in portfolio_assets:
                        asset_df = load_data(start_date, end_date, asset_ticker)
                        if asset_df.empty:
                            st.error(f"❌ {asset_ticker} 데이터를 불러오지 못했습니다.")
                            st.stop()
                        asset_data[asset_ticker] = asset_df
                generic_df = run_static_allocation_backtest(asset_data, portfolio_assets, initial_budget, fee_rate, slippage_rate)
                generic_label = "🧱 영구 포트폴리오" if strategy_choice == "영구 포트폴리오 전략" else "🌦️ 올웨더"
                if generic_df.empty:
                    st.error("❌ 포트폴리오 구성 자산의 공통 거래일 데이터가 부족합니다.")
                    st.stop()
                strategy_final_return = generic_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = generic_df['Hold_Cum_Return'].iloc[-1]
                strategy_final_balance = generic_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = generic_df['Hold_Balance'].iloc[-1]
                total_buys = np.sum(generic_df['Buy_Signal'])
                total_days = len(generic_df)
                 
            # 통합 비교 모드 연산 (두 개 모두 연산)
            else:
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size, _progress_container=progress_area)
                
                # 1. 머신러닝 예측 백테스트
                ml_df_predicted = run_ml_backtest(df, pred_series, initial_budget, fee_rate, slippage_rate, use_drip)
                
                # 2. 전체 기간 데이터프레임으로 확장 (앞쪽 학습 기간 90일 동안은 매매 없음/잔고 유지 처리)
                ml_df = pd.DataFrame(index=df.index)
                ml_df['Actual_Close'] = df['종가']
                ml_df['Predicted_Close'] = pred_series
                ml_df['Predicted_Close'] = ml_df['Predicted_Close'].fillna(df['종가'])
                
                for col in ['Strategy_Return', 'Hold_Return', 'Strategy_Cum_Return', 'Hold_Cum_Return', 'Strategy_Balance', 'Hold_Balance']:
                    if col in ml_df_predicted.columns:
                        ml_df[col] = ml_df_predicted[col]
                
                # NaN 값을 가진 앞쪽 학습 기간을 기본값(변동 없음)으로 채움
                ml_df['Strategy_Return'] = ml_df['Strategy_Return'].fillna(1.0)
                
                # 단순 보유 수익률 계산
                if use_drip and '배당금' in df.columns:
                    div_yield = df['배당금'] / df['종가'].shift(1).fillna(df['종가'])
                else:
                    div_yield = 0.0
                hold_returns = (df['종가'] / df['종가'].shift(1).fillna(df['종가'])) + div_yield
                hold_returns = hold_returns.fillna(1.0)
                hold_returns_array = hold_returns.values
                if len(hold_returns_array) > 0:
                    hold_returns_array[0] = hold_returns_array[0] - (fee_rate + slippage_rate) / 100
                ml_df['Hold_Return'] = hold_returns_array
                
                # 전체 누적 값 재산출
                ml_df['Strategy_Cum_Return'] = (ml_df['Strategy_Return'].cumprod() - 1) * 100
                ml_df['Hold_Cum_Return'] = (ml_df['Hold_Return'].cumprod() - 1) * 100
                ml_df['Strategy_Balance'] = initial_budget * ml_df['Strategy_Return'].cumprod()
                ml_df['Hold_Balance'] = initial_budget * ml_df['Hold_Return'].cumprod()
                
                # 3. 변동성 돌파도 전체 기간으로 사용
                vbt_df = run_vbt_backtest(df, K, initial_budget, fee_rate, slippage_rate, use_drip)
                actual_close = df['종가']
                
                ml_final_return = ml_df['Strategy_Cum_Return'].iloc[-1]
                vbt_final_return = vbt_df['Strategy_Cum_Return'].iloc[-1]
                hold_final_return = ml_df['Hold_Cum_Return'].iloc[-1]
                
                ml_final_balance = ml_df['Strategy_Balance'].iloc[-1]
                vbt_final_balance = vbt_df['Strategy_Balance'].iloc[-1]
                hold_final_balance = ml_df['Hold_Balance'].iloc[-1]
                
                # 예측 오차는 예측이 존재했던 구간에서만 평균 계산
                mae = (df['종가'].loc[pred_series.index] - pred_series).abs().mean()
                 
            run_status_message.success(f"✅ 백테스트 완료: {ticker_name} ({ticker_symbol}) / {strategy_choice}")

            # --- 구조 1: 성과 지표 (Metrics 4개) ---
            st.subheader("✅ 백테스트 결과 요약")
            st.caption(f"{ticker_name} ({ticker_symbol}) | {start_date} ~ {end_date} | {strategy_choice}")
            col1, col2, col3, col4 = st.columns(4)
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                with col1:
                    st.metric(label="🤖 머신러닝 최종 잔고 (수익률)", value=f"{strategy_final_balance:,.0f} 원", delta=f"{strategy_final_return:+.2f}%")
                with col2:
                    st.metric(label="📈 단순 보유 최종 잔고 (수익률)", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col3:
                    st.metric(label="📊 평균 절대 오차 (MAE)", value=f"{mae:,.0f} 원", delta=f"오차율(MAPE): {mape:.2f}%", delta_color="inverse")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")
                    
            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                strategy_label_map = {
                    "변동성 돌파 전략 (Larry Williams)": "⚡ 변동성 돌파",
                    "듀얼 모멘텀 전략": "🧭 듀얼 모멘텀",
                    "이동평균선 골든크로스 전략": "📈 이동평균선 크로스",
                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드",
                    "MACD 추세 전략": "📊 MACD 추세",
                }
                strategy_label_name = strategy_label_map[strategy_choice] if strategy_choice in strategy_label_map else generic_label
                with col1:
                    st.metric(label=f"{strategy_label_name} 최종 잔고 (수익률)", value=f"{strategy_final_balance:,.0f} 원", delta=f"{strategy_final_return:+.2f}%")
                with col2:
                    st.metric(label="📈 단순 보유 최종 잔고 (수익률)", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col3:
                    st.metric(label="🛒 총 매매 거래 횟수", value=f"{total_buys} 회", delta=f"참여율: {(total_buys/total_days)*100:.1f}%")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{total_days} 일")
                    
            else: # 통합 비교 모드
                with col1:
                    st.metric(label="🤖 머신러닝 최종 잔고", value=f"{ml_final_balance:,.0f} 원", delta=f"{ml_final_return:+.2f}%")
                with col2:
                    st.metric(label="⚡ 변동성 돌파 최종 잔고", value=f"{vbt_final_balance:,.0f} 원", delta=f"{vbt_final_return:+.2f}%")
                with col3:
                    st.metric(label="📈 단순 보유 최종 잔고", value=f"{hold_final_balance:,.0f} 원", delta=f"{hold_final_return:+.2f}%")
                with col4:
                    st.metric(label="⏳ 총 분석 영업일 수", value=f"{len(ml_df)} 일")

            # --- 구조 2: 주가 비교 차트 ---
            if strategy_choice == "머신러닝 롤링 예측 전략":
                st.subheader(f"🔮 실제 {ticker_name} 종가 vs 예측 주가 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                st.subheader(f"🏷️ 실제 {ticker_name} 주가 vs 매수 목표가(Buy Target)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="매수 목표가 (시가 + Range * K)", 
                    line=dict(color="#d62728", width=1.5, dash="dash"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)

            elif strategy_choice == "듀얼 모멘텀 전략":
                st.subheader("🧭 듀얼 모멘텀 가격 비교 및 리밸런싱")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=dm_df.index, y=dm_df['Attack_Close'], name=f"공격 자산 ({ticker_symbol})",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>공격 자산</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=dm_df.index, y=dm_df['Defense_Close'], name=f"비교/방어 자산 ({defense_ticker_code.strip().upper()})",
                    line=dict(color="#2ca02c", width=2),
                    hovertemplate='<b>비교/방어 자산</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                allocation_markers = dm_df[dm_df['Position'] != dm_df['Position'].shift(1).fillna("CASH")]
                fig_price.add_trace(go.Scatter(
                    x=allocation_markers.index,
                    y=allocation_markers['Attack_Close'],
                    mode="markers",
                    name="리밸런싱",
                    marker=dict(color="#d62728", size=8, symbol="diamond"),
                    customdata=allocation_markers['Selected_Asset'],
                    hovertemplate='<b>리밸런싱</b><br>날짜: %{x}<br>선택: %{customdata}<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="가격"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)

            elif strategy_choice == "이동평균선 골든크로스 전략":
                st.subheader(f"📈 실제 {ticker_name} 주가 및 이동평균선(SMA)")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Short'], name=f"단기 SMA ({ma_short}일)", 
                    line=dict(color="#ff7f0e", width=1.5),
                    hovertemplate='<b>단기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['SMA_Long'], name=f"장기 SMA ({ma_long}일)", 
                    line=dict(color="#2ca02c", width=1.5),
                    hovertemplate='<b>장기 SMA</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)

            elif strategy_choice == "RSI 과매도 반등 전략":
                st.subheader(f"🔄 실제 {ticker_name} 주가 및 RSI 보조지표")
                
                # 1. 주가 차트
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title=""),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
                # 2. RSI 차트
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['RSI'], name="RSI",
                    line=dict(color="#9467bd", width=1.5),
                    hovertemplate='<b>RSI</b><br>날짜: %{x}<br>수치: %{y:.1f}<extra></extra>'
                ))
                fig_rsi.add_hline(y=buy_rsi, line_dash="dash", line_color="green", annotation_text=f"과매도 기준 ({buy_rsi})")
                fig_rsi.add_hline(y=sell_rsi, line_dash="dash", line_color="red", annotation_text=f"과매도 기준 ({sell_rsi})")
                fig_rsi.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=10, b=20),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", range=[0, 100], title="RSI"),
                    height=180
                )
                st.plotly_chart(fig_rsi, use_container_width=True)

            elif strategy_choice == "볼린저 밴드 반등 전략":
                st.subheader(f"🔘 실제 {ticker_name} 주가 및 볼린저 밴드")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Mid'], name="중간선 (SMA)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>중간선</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Upper_Band'], name="상단 밴드", 
                    line=dict(color="#2ca02c", width=1),
                    hovertemplate='<b>상단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Lower_Band'], name="하단 밴드", 
                    line=dict(color="#d62728", width=1),
                    hovertemplate='<b>하단 밴드</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)

            elif strategy_choice == "MACD 추세 전략":
                st.subheader(f"📊 실제 {ticker_name} 주가 및 MACD 신호 지표")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['종가'], name="실제 종가",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title=""),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=300
                )
                st.plotly_chart(fig_price, use_container_width=True)

                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['MACD'], name="MACD선",
                    line=dict(color="#9467bd", width=1.5),
                    hovertemplate='<b>MACD선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Signal'], name="Signal선",
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>Signal선</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                colors = np.where(macd_df['Histogram'] >= 0, '#2ca02c', '#d62728')
                fig_macd.add_trace(go.Bar(
                    x=macd_df.index, y=macd_df['Histogram'], name="오실레이터",
                    marker_color=colors,
                    hovertemplate='<b>오실레이터</b><br>날짜: %{x}<br>수치: %{y:.2f}<extra></extra>'
                ))
                fig_macd.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=10, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="MACD 수치"),
                    height=220
                )
                st.plotly_chart(fig_macd, use_container_width=True)

            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                st.subheader(f"{generic_label} 가격 및 신호")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['종가'], name="기준 가격",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>기준 가격</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                signal_points = generic_df[generic_df['Buy_Signal'] & (~generic_df['Buy_Signal'].shift(1).fillna(False))]
                fig_price.add_trace(go.Scatter(
                    x=signal_points.index, y=signal_points['종가'], mode="markers",
                    name="진입/리밸런싱", marker=dict(color="#2ca02c", size=8, symbol="triangle-up"),
                    hovertemplate='<b>신호</b><br>날짜: %{x}<br>가격: %{y:,.2f}<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="가격"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)
                 
            else: # 통합 비교 모드
                st.subheader(f"📊 실제 {ticker_name} 주가 및 전략별 신호선 비교")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df.index, y=df['종가'], name="실제 종가", 
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate='<b>실제 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=pred_series.index, y=pred_series, name="예측 종가 (머신러닝)", 
                    line=dict(color="#ff7f0e", width=1.5, dash="dash"),
                    hovertemplate='<b>예측 종가</b><br>날짜: %{x}<br>가격: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Buy_Target'], name="돌파 매수 목표가 (VBT)", 
                    line=dict(color="#d62728", width=1.5, dash="dot"),
                    hovertemplate='<b>매수 목표가</b><br>날짜: %{x}<br>목표가: %{y:,.0f}원<extra></extra>'
                ))
                fig_price.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                    yaxis=dict(showgrid=True, gridcolor="#e9ecef", tickformat=",", title="주가"),
                    height=400
                )
                st.plotly_chart(fig_price, use_container_width=True)

            # --- 구조 3: 누적 수익률 비교 추이 그래프 ---
            st.subheader("📈 백테스트 누적 수익률 비교 추이")
            fig_ret = go.Figure()
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Strategy_Cum_Return'], name="🤖 머신러닝 예측 전략", 
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>머신러닝 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Strategy_Cum_Return'], name="⚡ 변동성 돌파 전략", 
                    line=dict(color="#9467bd", width=2.5),
                    hovertemplate='<b>변동성 돌파 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "듀얼 모멘텀 전략":
                fig_ret.add_trace(go.Scatter(
                    x=dm_df.index, y=dm_df['Strategy_Cum_Return'], name="🧭 듀얼 모멘텀 전략",
                    line=dict(color="#bcbd22", width=2.5),
                    hovertemplate='<b>듀얼 모멘텀</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=dm_df.index, y=dm_df['Hold_Cum_Return'], name=f"📈 공격 자산 단순 보유 ({ticker_symbol})",
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>공격 자산 단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "이동평균선 골든크로스 전략":
                fig_ret.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['Strategy_Cum_Return'], name="📈 이동평균 크로스 전략", 
                    line=dict(color="#ff7f0e", width=2.5),
                    hovertemplate='<b>이동평균 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=ma_df.index, y=ma_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "RSI 과매도 반등 전략":
                fig_ret.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['Strategy_Cum_Return'], name="🔄 RSI 반등 전략", 
                    line=dict(color="#9467bd", width=2.5),
                    hovertemplate='<b>RSI 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=rsi_df.index, y=rsi_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "볼린저 밴드 반등 전략":
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Strategy_Cum_Return'], name="🔘 볼린저 밴드 전략", 
                    line=dict(color="#17becf", width=2.5),
                    hovertemplate='<b>볼린저 밴드 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=bb_df.index, y=bb_df['Hold_Cum_Return'], name="📈 단순 보유", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice == "MACD 추세 전략":
                fig_ret.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Strategy_Cum_Return'], name="📊 MACD 추세 전략",
                    line=dict(color="#e377c2", width=2.5),
                    hovertemplate='<b>MACD 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=macd_df.index, y=macd_df['Hold_Cum_Return'], name="📈 단순 보유",
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            elif strategy_choice in ["스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                fig_ret.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['Strategy_Cum_Return'], name=generic_label,
                    line=dict(color="#1f77b4", width=2.5),
                    hovertemplate='<b>전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=generic_df.index, y=generic_df['Hold_Cum_Return'], name="📈 기준 자산 단순 보유",
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
            else: # 통합 비교 모드
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Strategy_Cum_Return'], name="🤖 머신러닝 예측 전략", 
                    line=dict(color="#2ca02c", width=2.5),
                    hovertemplate='<b>머신러닝 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=vbt_df.index, y=vbt_df['Strategy_Cum_Return'], name="⚡ 변동성 돌파 전략", 
                    line=dict(color="#9467bd", width=2.5),
                    hovertemplate='<b>변동성 돌파 전략</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                fig_ret.add_trace(go.Scatter(
                    x=ml_df.index, y=ml_df['Hold_Cum_Return'], name="📈 단순 보유 (Buy & Hold)", 
                    line=dict(color="#7f7f7f", width=1.5, dash="dot"),
                    hovertemplate='<b>단순 보유</b><br>날짜: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                ))
                
            fig_ret.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#e9ecef", title="날짜"),
                yaxis=dict(showgrid=True, gridcolor="#e9ecef", title="누적 수익률 (%)"),
                height=400
            )
            st.plotly_chart(fig_ret, use_container_width=True)

            # --- 구조 4: 월별 분석 차트 및 통계 테이블 (2열 분할 구성) ---
            st.subheader("📅 상세 요약 및 월별 분석")
            
            col_chart, col_table = st.columns([2, 1])
            
            if strategy_choice == "머신러닝 롤링 예측 전략":
                monthly_stats = calculate_ml_monthly_stats(actual_close, pred_series, ml_df)
                with col_chart:
                    fig_bar = px.bar(
                        monthly_stats, x='년-월', y='평균 절대 오차 (원)', 
                        color='평균 절대 오차 (원)',
                        color_continuous_scale=px.colors.sequential.OrRd
                    )
                    fig_bar.update_traces(hovertemplate='<b>년-월</b>: %{x}<br><b>평균 절대 오차</b>: %{y:,.0f}원<extra></extra>')
                    fig_bar.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(type='category', title="년-월"),
                        yaxis=dict(tickformat=",", title="평균 오차 (원)"),
                        coloraxis_colorbar=dict(title="오차 (원)"),
                        height=350
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📊 **월별 통계 요약 데이터**")
                    display_df = monthly_stats.copy()
                    display_df['평균 절대 오차 (원)'] = display_df['평균 절대 오차 (원)'].map('{:,.0f}원'.format)
                    display_df['평균 오차율 (%)'] = display_df['평균 오차율 (%)'].map('{:.2f}%'.format)
                    display_df['월간 수익률 (%)'] = display_df['월간 수익률 (%)'].map('{:+.2f}%'.format)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "듀얼 모멘텀 전략", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략", "MACD 추세 전략", "스토캐스틱 오실레이터 전략", "일목균형표 전환/기준선 전략", "ADX/DMI 추세 전략", "엔벨로프 반등 전략", "영구 포트폴리오 전략", "올웨더 포트폴리오 전략"]:
                if strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                    summary_stats = calculate_vbt_monthly_stats(vbt_df)
                    target_df = vbt_df
                elif strategy_choice == "듀얼 모멘텀 전략":
                    summary_stats = calculate_dual_momentum_monthly_stats(dm_df)
                    target_df = dm_df
                elif strategy_choice == "이동평균선 골든크로스 전략":
                    summary_stats = calculate_ma_cross_monthly_stats(ma_df)
                    target_df = ma_df
                elif strategy_choice == "RSI 과매도 반등 전략":
                    summary_stats = calculate_rsi_monthly_stats(rsi_df)
                    target_df = rsi_df
                elif strategy_choice == "볼린저 밴드 반등 전략":
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df
                elif strategy_choice == "MACD 추세 전략":
                    summary_stats = calculate_macd_monthly_stats(macd_df)
                    target_df = macd_df
                else:
                    summary_stats = calculate_signal_monthly_stats(generic_df)
                    target_df = generic_df
                    
                with col_chart:
                    fig_bar = px.bar(
                        target_df, x=target_df.index, y='Daily_Return_Pct',
                        color='Daily_Return_Pct',
                        color_continuous_scale=px.colors.diverging.RdYlGn,
                        color_continuous_midpoint=0.0
                    )
                    fig_bar.update_traces(hovertemplate='<b>날짜</b>: %{x}<br><b>일별 수익률</b>: %{y:.2f}%<extra></extra>')
                    fig_bar.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(title="날짜"),
                        yaxis=dict(title="일별 수익률 (%)"),
                        coloraxis_colorbar=dict(title="수익률 (%)"),
                        height=350
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📅 **월별 거래 요약 데이터**")
                    display_stats = summary_stats.copy()
                    if '매수 보유 일수 (일)' in display_stats.columns:
                        display_stats['매수 보유 일수 (일)'] = display_stats['매수 보유 일수 (일)'].map('{:,.0f}일'.format)
                    if '매수 횟수 (회)' in display_stats.columns:
                        display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    if '공격 모멘텀 (%)' in display_stats.columns:
                        display_stats['공격 모멘텀 (%)'] = display_stats['공격 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    if '방어 모멘텀 (%)' in display_stats.columns:
                        display_stats['방어 모멘텀 (%)'] = display_stats['방어 모멘텀 (%)'].map(lambda x: "" if pd.isna(x) else f"{x:+.2f}%")
                    display_stats['전략 수익률 (%)'] = display_stats['전략 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['단순 보유 수익률 (%)'] = display_stats['단순 보유 수익률 (%)'].map('{:+.2f}%'.format)
                    st.dataframe(display_stats, use_container_width=True, hide_index=True)
                    
            else: # 통합 비교 모드
                combined_stats = calculate_combined_monthly_stats(ml_df, vbt_df)
                with col_chart:
                    fig_monthly_bar = go.Figure()
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['머신러닝 수익률 (%)'],
                        name="🤖 머신러닝", marker_color="#2ca02c",
                        hovertemplate='<b>머신러닝 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['변동성 돌파 수익률 (%)'],
                        name="⚡ 변동성 돌파", marker_color="#9467bd",
                        hovertemplate='<b>변동성 돌파 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.add_trace(go.Bar(
                        x=combined_stats['년-월'], y=combined_stats['단순 보유 수익률 (%)'],
                        name="📈 단순 보유", marker_color="#7f7f7f",
                        hovertemplate='<b>단순 보유 월수익률</b><br>년-월: %{x}<br>수익률: %{y:.2f}%<extra></extra>'
                    ))
                    fig_monthly_bar.update_layout(
                        barmode='group', plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(type='category', title="년-월"),
                        yaxis=dict(title="월간 수익률 (%)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=350
                    )
                    st.plotly_chart(fig_monthly_bar, use_container_width=True)
                    
                with col_table:
                    st.write("📊 **월별 전략별 수익률 대조 테이블**")
                    display_stats = combined_stats.copy()
                    display_stats['머신러닝 수익률 (%)'] = display_stats['머신러닝 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['변동성 돌파 수익률 (%)'] = display_stats['변동성 돌파 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['단순 보유 수익률 (%)'] = display_stats['단순 보유 수익률 (%)'].map('{:+.2f}%'.format)
                    display_stats['돌파 매수 횟수 (회)'] = display_stats['돌파 매수 횟수 (회)'].map('{:,.0f}회'.format)
                    display_stats['머신러닝 오차 (원)'] = display_stats['머신러닝 오차 (원)'].map('{:,.0f}원'.format)
                    st.dataframe(display_stats, use_container_width=True, hide_index=True)

            st.divider()
            render_financial_data_section(ticker_code, ticker_name)

    else:
        st.info("👈 왼쪽 사이드바에서 [백테스트 실행하기] 버튼을 눌러주세요!")
