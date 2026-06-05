import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path

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
    'Operating Income': '영업이익', 
    'Net Income': '당기순이익',
    'Total Assets': '총자산', 
    'Total Liabilities Net Minority Interest': '총부채', 
    'Stockholders Equity': '자본총계',
    'Operating Cash Flow': '영업활동현금흐름', 
    'Free Cash Flow': '잉여현금흐름'
}

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


def configure_yfinance_cache(yf):
    """yfinance가 쓰는 로컬 캐시를 프로젝트 내부로 고정합니다."""
    cache_dir = Path(__file__).resolve().parents[1] / ".cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))


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

    # [LOG: 20260605_1552] 입력값이 6자리 숫자로 구성된 한국 종목코드인 경우 즉시 반환하여 매핑 오작동 방지
    if key.isdigit() and len(key) == 6:
        return key

    # [LOG: 20260605_1557] 영문 및 일부 특수문자(. ^)로만 구성된 순수 해외 티커의 경우 한국 상장사 부분매칭을 건너뛰고 즉시 반환
    import re
    if re.match(r'^[a-zA-Z\.\^]+$', key):
        return ticker_input.strip()

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
    """네이버 금융 시가총액 페이지에서 한국 거래소(KOSPI, KOSDAQ) 전체 상장사 목록(우선주 포함)을 가져오고,
    네이버 금융에서 전체 ETF 목록을 가져와 병합합니다.
    장애 발생 시 로컬 백업 파일(listed_stocks_backup.csv)에서 불러와 안정적인 검색을 상시 지원합니다.
    """
    import requests
    from io import StringIO
    import re
    
    # [LOG: 20260605_1542] 스트림릿 클라우드 크롤링 차단 대응 및 백업 파일 보호 처리
    backup_path = Path(__file__).parent / "listed_stocks_backup.csv"
    df_stocks = pd.DataFrame()
    df_etfs = pd.DataFrame()
    
    # 1. 네이버 금융 시가총액 페이지에서 코스피/코스닥 상장 주식 로드 (우선주 포함)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        stocks_list = []
        
        # sosok=0 (코스피), sosok=1 (코스닥)
        for sosok in [0, 1]:
            page = 1
            while True:
                url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
                res = requests.get(url, headers=headers, timeout=5)
                res.encoding = 'euc-kr'
                
                # [LOG: 20260605_1546] HTML에서 종목코드와 종목명을 안전하게 한 쌍으로 추출하여 매핑 뒤틀림 방지
                matches = re.findall(r'<a href="/item/main\.naver\?code=(\d{6})"[^>]* class="tltle">([^<]+)</a>', res.text)
                if not matches:
                    break
                
                for ticker, name in matches:
                    stocks_list.append({
                        'name': name.strip(),
                        'ticker': ticker.strip().zfill(6)
                    })
                
                page += 1
                
        if stocks_list:
            df_stocks = pd.DataFrame(stocks_list)
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

    # 3. 실시간 일반 주식 크롤링(df_stocks)이 실패하여 비어 있는 경우 백업 파일에서 안전하게 복구
    is_live_stocks_loaded = not df_stocks.empty
    
    if not is_live_stocks_loaded:
        # 일반 주식 크롤링 실패 시 로컬 백업 파일에서 주식 목록을 가져옵니다. (운영체제 구분 없이 인코딩 고정)
        if backup_path.exists():
            try:
                df_backup = pd.read_csv(backup_path, encoding='utf-8-sig', dtype={'ticker': str})
                df_backup['ticker'] = df_backup['ticker'].astype(str).str.zfill(6)
                
                # 백업 데이터에서 ETF(보통 500000 이상 또는 이름에 ETF 포함)를 제외한 일반 주식 목록 추출
                if not df_etfs.empty:
                    etf_tickers = set(df_etfs['ticker'].tolist())
                    df_stocks = df_backup[~df_backup['ticker'].isin(etf_tickers)]
                else:
                    df_stocks = df_backup
            except Exception:
                pass

    # 4. 주식 및 ETF 병합
    df_merged = pd.DataFrame()
    if not df_stocks.empty or not df_etfs.empty:
        if df_stocks.empty:
            df_merged = df_etfs
        elif df_etfs.empty:
            df_merged = df_stocks
        else:
            df_merged = pd.concat([df_stocks, df_etfs], ignore_index=True)
            df_merged = df_merged.drop_duplicates(subset=['ticker'], keep='first')

    # 5. 오직 실시간 일반 주식 크롤링이 성공했을 때만 로컬 백업 파일을 최신으로 안전하게 갱신
    if is_live_stocks_loaded and not df_merged.empty:
        try:
            df_merged.to_csv(backup_path, index=False, encoding='utf-8-sig')
        except Exception:
            pass

    if not df_merged.empty:
        return df_merged

    # 6. 최종적으로 모든 경로가 실패했을 때 백업 파일 전체를 로드하여 최후의 수단으로 반환 (인코딩 고정)
    if backup_path.exists():
        try:
            df_backup = pd.read_csv(backup_path, encoding='utf-8-sig', dtype={'ticker': str})
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
        # [LOG: 20260605_1550] 종목코드(ticker)로도 검색이 가능하도록 매칭 범위 확장
        filtered = listed_df[listed_df.apply(lambda r: match_tokens(r['name']) or match_tokens(r['ticker']), axis=1)]
        for _, row in filtered.iterrows():
            ticker = row['ticker']
            name = row['name']
            if not any(m['ticker'] == ticker for m in matches):
                matches.append({"ticker": ticker, "name": name})

    # 3. 정렬 순서 최적화: 검색어 기반 스마트 정렬 (Score System)
    # 0순위: 완전 일치, 1순위: 검색어로 시작함, 2순위: 검색어 포함, 3순위: 그 외
    # [LOG: 20260605_1550] 정렬 점수 산정 시 종목코드(ticker) 매칭 가중치 추가 반영
    def score_match(query_str, name_str, ticker_str):
        q = query_str.lower().replace(" ", "")
        n = name_str.lower().replace(" ", "")
        t = ticker_str.lower().replace(" ", "")
        translated_q = group_translation.get(q, None)
        
        if q == n or q == t or (translated_q and translated_q == n):
            return 0
        elif n.startswith(q) or t.startswith(q) or (translated_q and n.startswith(translated_q)):
            return 1
        elif q in n or q in t or (translated_q and translated_q in n):
            return 2
        return 3

    matches = sorted(matches, key=lambda x: (score_match(key, x['name'], x['ticker']), len(x['name']), x['name']))

    return matches


@st.cache_data(ttl=86400)
def get_ticker_name(ticker_code):
    """종목 코드를 받아 종목명을 반환합니다. (KIND/Naver ETF DB 조회 -> yfinance -> pykrx 순)"""
    ticker_code = ticker_code.strip()
    if not ticker_code:
        return UNKNOWN_TICKER_NAME
    
    # [LOG: 20260605_1553] 미국 주식 티커(특수문자 포함) 지원을 위해 판별 로직 보완
    is_valid_us_ticker = ticker_code.isascii() and not (len(ticker_code) == 6 and ticker_code.isdigit())
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
    if is_valid_us_ticker:
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
    
    # [LOG: 20260605_1558] 사용자가 입력한 날짜에서 대시(-), 온점(.), 슬래시(/) 등 특수기호를 제거하여 정밀 수치 규격화
    import re
    start_date = re.sub(r'[^0-9]', '', str(start_date))
    end_date = re.sub(r'[^0-9]', '', str(end_date))
    
    # [LOG: 20260605_1020] yfinance download 시 배당금 데이터(actions=True) 반영
    # [LOG: 20260605_1553] 미국 주식 티커(특수문자 포함) 지원을 위해 판별 로직 보완
    if ticker_code.isascii() and not (len(ticker_code) == 6 and ticker_code.isdigit()):
        try:
            import yfinance as yf
            configure_yfinance_cache(yf)
            start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            df = yf.download(ticker_code.upper(), start=start_yf, end=end_yf, actions=True)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                df = df.rename(columns={
                    'Open': '시가',
                    'High': '고가',
                    'Low': '저가',
                    'Close': '종가',
                    'Volume': '거래량',
                    'Dividends': '배당금'
                })
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df
        except Exception as e:
            st.error(f"미국 주식 yfinance 데이터 로드 실패: {e}")
            return pd.DataFrame()
            
    # 2. 한국 주식/ETF (숫자 코드) 데이터 로드
    # pykrx의 잦은 차단/장애(EXPECTING VALUE 에러)를 방어하기 위해 yfinance(.KS/.KQ)를 최우선으로 다운로드합니다.
    if len(ticker_code) == 6 and ticker_code.isdigit():
        start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        for suffix in [".KS", ".KQ"]:
            try:
                import yfinance as yf
                configure_yfinance_cache(yf)
                df = yf.download(f"{ticker_code}{suffix}", start=start_yf, end=end_yf, actions=True)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [col[0] for col in df.columns]
                    df = df.rename(columns={
                        'Open': '시가',
                        'High': '고가',
                        'Low': '저가',
                        'Close': '종가',
                        'Volume': '거래량',
                        'Dividends': '배당금'
                    })
                    df.index = pd.to_datetime(df.index).tz_localize(None)
                    return df
            except Exception:
                pass
                
    # 3. 마지막 백업 수단: pykrx
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker_code)
        if not df.empty:
            # [LOG: 20260605_1556] pykrx 복구 시 배당금 컬럼 부재로 인한 KeyError 방지
            if "배당금" not in df.columns:
                df["배당금"] = 0.0
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
                for item in ['Total Assets', 'Total Liabilities Net Minority Interest', 'Stockholders Equity']:
                    if item in bs.index:
                        combined_data[item] = bs.loc[item]
            
            # financials 항목
            if fin is not None and not fin.empty:
                for item in ['Total Revenue', 'Operating Income', 'Net Income']:
                    if item in fin.index:
                        combined_data[item] = fin.loc[item]
                        
            # cashflow 항목
            if cf is not None and not cf.empty:
                for item in ['Operating Cash Flow', 'Free Cash Flow']:
                    if item in cf.index:
                        combined_data[item] = cf.loc[item]
            
            if combined_data:
                # 데이터프레임 빌드 및 전치
                df_fin = pd.DataFrame(combined_data)
                
                # 만약 칼럼이 Datetime 인덱스라면 연도로 포맷
                formatted_cols = []
                for col in df_fin.columns:
                    try:
                        formatted_cols.append(pd.to_datetime(col).strftime('%Y년'))
                    except Exception:
                        formatted_cols.append(str(col))
                df_fin.columns = formatted_cols
                
                # 한글 매핑 적용하여 리인덱스
                df_fin = df_fin.rename(index=FINANCIALS_KR)
                
                # 전치해서 반환 (행: 년도, 열: 재무항목)
                return df_fin.T
        except Exception:
            continue
            
    return pd.DataFrame()


# 3. 머신러닝 피처 및 타겟 전처리 함수
def prepare_features(df):
    """머신러닝 학습에 필요한 특성과 타겟을 설정합니다. 타겟은 종가(Close)입니다."""
    X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
    y = df['종가'].iloc[1:]
    return X, y

# 4. 머신러닝 롤링 윈도우 예측 수행 함수
@st.cache_data
def run_rolling_forecast(X, y, window_size):
    """매일 이전 window_size일의 데이터를 학습하여 다음 날 종가를 예측합니다. 
    동일한 피처와 윈도우 크기일 경우 연산 결과를 캐싱하여 즉시 반환합니다.
    """
    predictions = []
    prediction_dates = []
    
    # 진행 상황 표시줄
    progress_bar = st.progress(0)
    status_text = st.empty()
    
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
    # [LOG: 20260605_0950]
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    round_trip_cost = 2 * cost_rate
    
    vbt_df = df.copy()
    
    # OHLC 데이터 검증 (고가와 저가가 95% 이상 같은지 체크하여 종가만 채워진 부실 데이터 판별)
    is_invalid_ohlc = (vbt_df['고가'] == vbt_df['저가']).mean() > 0.95
    if is_invalid_ohlc:
        st.session_state['vbt_warning'] = "⚠️ 경고: 현재 종목 데이터는 시가/고가/저가가 누락되어 종가로 채워진 '간소화/변형 버전' 데이터입니다. 래리 윌리엄스의 변동성 돌파 전략이 정상적으로 작동하지 않을 수 있습니다."
    else:
        st.session_state['vbt_warning'] = None
        
    # 변동성 폭 계산 (전일 고가 - 전일 저가)
    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)
    
    # 매수 목표가 계산 (당일 시가 + 변동폭 * K)
    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)
    
    # 매수 조건: 당일 고가가 매수 목표가를 초과했는지 판별
    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']
    
    # 실제 매수 체결 가격 계산 (당일 시가가 목표가보다 높게 시작하면 시가에 체결, 그렇지 않으면 목표가 지정가 체결)
    vbt_df['Buy_Price'] = np.where(
        vbt_df['시가'] > vbt_df['Buy_Target'],
        vbt_df['시가'],
        vbt_df['Buy_Target']
    )
    
    # [LOG: 20260605_1020] 배당금 재투자 (DRIP) 반영 조건 설정
    if use_drip and '배당금' in vbt_df.columns:
        div_yield = vbt_df['배당금'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])
        strategy_div_yield = np.where(vbt_df['Buy_Signal'], div_yield, 0.0)
    else:
        div_yield = 0.0
        strategy_div_yield = 0.0
        
    # 전략 일별 수익률 계산 (매수 체결 시 당일 종가 / 실제 매수 체결가 - 왕복 비용 + 배당 수익률 반영, 미체결 시 1.0)
    vbt_df['Strategy_Return'] = np.where(
        vbt_df['Buy_Signal'],
        (vbt_df['종가'] / vbt_df['Buy_Price']) - round_trip_cost + strategy_div_yield,
        1.0
    )
    
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
            st.session_state["run_backtest"] = True
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
    # [LOG: 20260605_1554] Rerun 시 선택 상태가 초기화되지 않도록 명시적 세션 키 부여
    selected_match_label = st.sidebar.selectbox(
        "검색된 종목 중 선택",
        options=[f"{match['name']} ({match['ticker']})" for match in ticker_matches],
        index=0,
        key="selected_search_match"
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

# 🚀 백테스트 실행 버튼 위치를 상단(종목 코드 바로 아래, 시작 날짜 위)으로 이동
run_button_clicked = st.sidebar.button("🚀 백테스트 실행하기", use_container_width=True)
if run_button_clicked:
    st.session_state['run_backtest'] = True

st.sidebar.header("⚙️ 전략 및 파라미터 설정")

# 1. 라디오 버튼을 사용하여 전략 및 통합 모드 선택 (3개 옵션 제공)
strategy_choice = st.sidebar.radio(
    "💡 분석할 전략 선택",
    options=[
        "머신러닝 롤링 예측 전략",
        "변동성 돌파 전략 (Larry Williams)",
        "두 전략 통합 비교",
        "이동평균선 골든크로스 전략",
        "RSI 과매도 반등 전략",
        "볼린저 밴드 반등 전략"
    ]
)

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

# 데이터 로딩 로직 최적화: 종목이나 기간이 바뀐 최초 1회에만 데이터 로드 스피너가 작동
if not is_known_ticker:
    st.session_state['stock_data'] = pd.DataFrame()
    st.session_state['loaded_ticker'] = ""
    st.session_state['loaded_start'] = ""
    st.session_state['loaded_end'] = ""
    st.session_state['run_backtest'] = False
elif not is_data_cached:
    with st.spinner(f"📡 {ticker_name} ({ticker_symbol}) 주식 데이터를 불러오는 중..."):
        df = load_data(start_date, end_date, ticker_code)
        if not df.empty:
            st.session_state['stock_data'] = df
            st.session_state['loaded_ticker'] = ticker_code.strip()
            st.session_state['loaded_start'] = start_date
            st.session_state['loaded_end'] = end_date
            # 종목이나 날짜만 바뀐 경우에는 이전 실행 상태를 리셋하되,
            # 버튼 실행 또는 리스트 행 선택으로 들어온 실행 요청은 유지
            if not run_button_clicked and not st.session_state.get('run_backtest', False):
                st.session_state['run_backtest'] = False
        else:
            st.session_state['stock_data'] = pd.DataFrame()

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
        # 1. 1차 검증
        if strategy_choice in ["머신러닝 롤링 예측 전략", "두 전략 통합 비교"] and len(df) <= window_size:
            st.error(f"데이터의 총 크기({len(df)}일)가 학습 윈도우 크기({window_size}일)보다 작습니다. 기간을 늘려주세요.")
        else:
            # --- 백테스트 연산 수행 ---
            
            # 머신러닝 모드 연산
            if strategy_choice == "머신러닝 롤링 예측 전략":
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size)
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
                
            # 통합 비교 모드 연산 (두 개 모두 연산)
            else:
                X, y = prepare_features(df)
                pred_series = run_rolling_forecast(X, y, window_size)
                
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
                
            # [LOG: 20260605_0950] OHLC 유효성 검증 경고 표시
            if st.session_state.get('vbt_warning') and strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "두 전략 통합 비교"]:
                st.warning(st.session_state['vbt_warning'])
                
            # --- 구조 1: 성과 지표 (Metrics 4개) ---
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
                    
            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략"]:
                strategy_label_name = {
                    "변동성 돌파 전략 (Larry Williams)": "⚡ 변동성 돌파",
                    "이동평균선 골든크로스 전략": "📈 이동평균선 크로스",
                    "RSI 과매도 반등 전략": "🔄 RSI 반등",
                    "볼린저 밴드 반등 전략": "🔘 볼린저 밴드"
                }[strategy_choice]
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
                    
            elif strategy_choice in ["변동성 돌파 전략 (Larry Williams)", "이동평균선 골든크로스 전략", "RSI 과매도 반등 전략", "볼린저 밴드 반등 전략"]:
                if strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                    summary_stats = calculate_vbt_monthly_stats(vbt_df)
                    target_df = vbt_df
                elif strategy_choice == "이동평균선 골든크로스 전략":
                    summary_stats = calculate_ma_cross_monthly_stats(ma_df)
                    target_df = ma_df
                elif strategy_choice == "RSI 과매도 반등 전략":
                    summary_stats = calculate_rsi_monthly_stats(rsi_df)
                    target_df = rsi_df
                else:
                    summary_stats = calculate_bb_monthly_stats(bb_df)
                    target_df = bb_df
                    
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
                    # [LOG: 20260605_0950] 변동성 돌파 전략과 그 외 전략(보유 일수 기준)의 컬럼 포맷팅 분기 처리
                    if strategy_choice == "변동성 돌파 전략 (Larry Williams)":
                        if '매수 횟수 (회)' in display_stats.columns:
                            display_stats['매수 횟수 (회)'] = display_stats['매수 횟수 (회)'].map('{:,.0f}회'.format)
                    else:
                        if '매수 보유 일수 (일)' in display_stats.columns:
                            display_stats['매수 보유 일수 (일)'] = display_stats['매수 보유 일수 (일)'].map('{:,.0f}일'.format)
                    
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

            # --- 구조 5: 주요 재무 정보 표 노출 (yfinance 연동) ---
            st.divider()
            st.subheader(f"🏢 {ticker_name} ({ticker_code}) 주요 재무 정보")
            with st.spinner("재무 정보 데이터를 불러오는 중..."):
                df_financials = load_financial_data(ticker_code)
                if not df_financials.empty:
                    display_fin = df_financials.copy()
                    
                    # 수치형 값 예쁘게 쉼표 포맷팅
                    for col in display_fin.columns:
                        try:
                            display_fin[col] = display_fin[col].map(lambda x: f"{x:,.0f}" if pd.notnull(x) and not isinstance(x, str) else x)
                        except Exception:
                            pass
                    
                    st.dataframe(display_fin, use_container_width=True)
                    st.caption("※ 정보 제공: Yahoo Finance (연간 기준 재무 데이터)")
                else:
                    st.info("이 종목에 대한 연간 재무 정보(재무상태표/손익계산서/현금흐름표)를 불러올 수 없습니다.")
    else:
        st.info("👈 왼쪽 사이드바에서 [백테스트 실행하기] 버튼을 눌러주세요!")
