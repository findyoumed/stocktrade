# [LOG: 20260604_1952]
import os
import numpy as np
import pandas as pd
import streamlit as st
from pykrx import stock
from pathlib import Path
import yfinance as yf

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

def configure_yfinance_cache(yf_module):
    """yfinance가 쓰는 로컬 캐시를 프로젝트 내부로 고정합니다."""
    cache_dir = Path(__file__).resolve().parents[1] / ".cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf_module.set_tz_cache_location(str(cache_dir))

def normalize_search_text(value):
    return "".join(value.strip().lower().replace("-", " ").split())

def resolve_ticker_input(ticker_input):
    """회사명/별칭/영문 공식명을 실제 조회용 종목코드로 변환합니다."""
    if not ticker_input:
        return ""
    
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

    return ticker_input.strip()

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'
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
    """검색 쿼리를 기반으로 매칭되는 종목 리스트를 반환합니다."""
    key = normalize_search_text(query)
    if not key:
        return []

    import re
    tokens = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+|[가-힣]+', key) if t]
    if not tokens:
        tokens = [key.lower()]

    group_translation = {
        "lg": "엘지",
        "sk": "에스케이",
        "gs": "지에스",
        "cj": "씨제이",
        "hd": "현대",
    }

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
    
    for ticker, item in LOCAL_TICKER_CATALOG.items():
        searchable_values = [ticker, item["name"], *item.get("aliases", [])]
        for val in searchable_values:
            if match_tokens(val):
                matches.append({"ticker": ticker, "name": item["name"]})
                break

    listed_df = get_all_listed_stocks()
    if not listed_df.empty:
        # [LOG: 20260605_1550] 종목코드(ticker)로도 검색이 가능하도록 매칭 범위 확장
        filtered = listed_df[listed_df.apply(lambda r: match_tokens(r['name']) or match_tokens(r['ticker']), axis=1)]
        for _, row in filtered.iterrows():
            ticker = row['ticker']
            name = row['name']
            if not any(m['ticker'] == ticker for m in matches):
                matches.append({"ticker": ticker, "name": name})

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
    """종목 코드를 통해 매칭되는 한글/영문 사명을 탐색하여 반환합니다."""
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
        
    listed_df = get_all_listed_stocks()
    if not listed_df.empty:
        match = listed_df[listed_df['ticker'] == ticker_code]
        if not match.empty:
            return match.iloc[0]['name']

    if is_valid_us_ticker:
        try:
            configure_yfinance_cache(yf)
            ticker_info = yf.Ticker(ticker_code.upper()).info
            name = ticker_info.get('longName') or ticker_info.get('shortName')
            if name:
                return name
        except Exception:
            pass
        return UNKNOWN_TICKER_NAME
            
    try:
        name = stock.get_market_ticker_name(ticker_code)
        if name != "":
            return name
    except Exception:
        pass
        
    for suffix in [".KS", ".KQ"]:
        try:
            configure_yfinance_cache(yf)
            ticker_info = yf.Ticker(f"{ticker_code}{suffix}").info
            name = ticker_info.get('longName') or ticker_info.get('shortName')
            if name:
                return name
        except Exception:
            pass
        
    return UNKNOWN_TICKER_NAME

def get_dividends_df(ticker_code, start_date_str, end_date_str, trading_dates):
    """
    해당 종목의 배당(분배금) 이력을 수집하여 각 거래일(trading_dates)에 가깝게 Snap 보정한 Series를 반환합니다.
    """
    div_df = pd.DataFrame(columns=["date", "amount"])
    
    # 1. PLUS 고배당주(161510)인 경우 로컬 fallback 파일에서 우선 조회
    if ticker_code == "161510":
        csv_path = Path(__file__).parent / "dividends_fallback.csv"
        if csv_path.exists():
            try:
                div_df = pd.read_csv(csv_path)
                div_df["date"] = pd.to_datetime(div_df["date"]).dt.strftime("%Y-%m-%d")
                div_df["amount"] = pd.to_numeric(div_df["amount"], errors="coerce").fillna(0)
            except Exception:
                pass
                
    # 2. 그 외 종목이거나 로컬 로드 실패 시 yfinance 온라인 데이터 조회 시도
    if div_df.empty:
        symbols_to_try = [ticker_code.upper()]
        if len(ticker_code) == 6 and ticker_code.isdigit():
            symbols_to_try = [f"{ticker_code}.KS", f"{ticker_code}.KQ"]
            
        for sym in symbols_to_try:
            try:
                configure_yfinance_cache(yf)
                ticker_obj = yf.Ticker(sym)
                divs = ticker_obj.dividends
                if not divs.empty:
                    temp_df = divs.reset_index()
                    temp_df.columns = ["date", "amount"]
                    temp_df["date"] = pd.to_datetime(temp_df["date"]).dt.strftime("%Y-%m-%d")
                    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce").fillna(0)
                    div_df = temp_df
                    break
            except Exception:
                continue

    # 3. 빈 매핑용 Series 빌드 및 배당금 Snap 처리
    div_series = pd.Series(0.0, index=trading_dates)
    if div_df.empty:
        return div_series
        
    start_dt = pd.to_datetime(start_date_str).strftime("%Y-%m-%d")
    end_dt = pd.to_datetime(end_date_str).strftime("%Y-%m-%d")
    
    # 분석 대상 기간의 배당 정보 필터링
    div_df = div_df[(div_df["date"] >= start_dt) & (div_df["date"] <= end_dt)]
    if div_df.empty:
        return div_series
        
    sorted_dates = sorted(list(trading_dates))
    if not sorted_dates:
        return div_series
        
    for _, row in div_df.iterrows():
        div_date = row["date"]
        amount = float(row["amount"])
        if amount <= 0:
            continue
            
        # snap to trading day
        if div_date in trading_dates:
            snapped = div_date
        else:
            # 지급 당일 거래 정보가 없으면 직전 거래 영업일을 할당 (plus_dividend의 Snap 로직 이식)
            prior = [d for d in sorted_dates if d <= div_date]
            snapped = prior[-1] if prior else None
            
        if snapped:
            div_series[snapped] += amount
            
    return div_series

@st.cache_data
def load_data(start_date, end_date, ticker_code):
    """선택한 종목의 OHLCV 주가 데이터 및 배당 데이터를 병합하여 로드합니다."""
    ticker_code = ticker_code.strip()
    df = pd.DataFrame()
    
    # [LOG: 20260605_1553] 미국 주식 티커(특수문자 포함) 지원을 위해 판별 로직 보완
    if ticker_code.isascii() and not (len(ticker_code) == 6 and ticker_code.isdigit()):
        try:
            configure_yfinance_cache(yf)
            start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            df = yf.download(ticker_code.upper(), start=start_yf, end=end_yf)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                df = df.rename(columns={
                    'Open': '시가',
                    'High': '고가',
                    'Low': '저가',
                    'Close': '종가',
                    'Volume': '거래량'
                })
                df.index = pd.to_datetime(df.index).tz_localize(None)
        except Exception as e:
            st.error(f"미국 주식 yfinance 데이터 로드 실패: {e}")
            return pd.DataFrame()
            
    # 2. 한국 주식/ETF (6자리 숫자) 로드
    elif len(ticker_code) == 6 and ticker_code.isdigit():
        start_yf = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end_yf = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        for suffix in [".KS", ".KQ"]:
            try:
                configure_yfinance_cache(yf)
                df = yf.download(f"{ticker_code}{suffix}", start=start_yf, end=end_yf)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [col[0] for col in df.columns]
                    df = df.rename(columns={
                        'Open': '시가',
                        'High': '고가',
                        'Low': '저가',
                        'Close': '종가',
                        'Volume': '거래량'
                    })
                    df.index = pd.to_datetime(df.index).tz_localize(None)
                    break
            except Exception:
                pass
                
        # 3. 마지막 백업 수단: pykrx
        if df.empty:
            try:
                df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker_code)
            except Exception:
                pass

    # 4. 주가 데이터를 성공적으로 로드했다면 배당 데이터를 수집하여 병합
    if not df.empty:
        # DatetimeIndex를 문자열 날짜 리스트 형태로 변환하여 snap 인자로 매핑
        trading_dates = set(df.index.strftime("%Y-%m-%d"))
        div_series = get_dividends_df(ticker_code, start_date, end_date, trading_dates)
        
        # DatetimeIndex에 맞게 Series 인덱스 정렬 변환
        div_series.index = pd.to_datetime(div_series.index)
        df['배당금'] = div_series
        
    return df

@st.cache_data
def load_financial_data(ticker_code):
    """yfinance를 활용하여 연간 재무제표 정보를 가져옵니다."""
    tickers_to_try = [ticker_code]
    if len(ticker_code) == 6 and ticker_code.isdigit():
        tickers_to_try = [f"{ticker_code}.KS", f"{ticker_code}.KQ"]
        
    for ticker_symbol in tickers_to_try:
        try:
            configure_yfinance_cache(yf)
            tic = yf.Ticker(ticker_symbol)
            bs = tic.balance_sheet
            fin = tic.financials
            cf = tic.cashflow
            
            combined_data = {}
            
            if bs is not None and not bs.empty:
                for item in ['Total Assets', 'Total Liabilities Net Minority Interest', 'Stockholders Equity']:
                    if item in bs.index:
                        combined_data[item] = bs.loc[item]
            
            if fin is not None and not fin.empty:
                for item in ['Total Revenue', 'Operating Income', 'Net Income']:
                    if item in fin.index:
                        combined_data[item] = fin.loc[item]
                        
            if cf is not None and not cf.empty:
                for item in ['Operating Cash Flow', 'Free Cash Flow']:
                    if item in cf.index:
                        combined_data[item] = cf.loc[item]
            
            if combined_data:
                df_fin = pd.DataFrame(combined_data)
                
                formatted_cols = []
                for col in df_fin.columns:
                    try:
                        formatted_cols.append(pd.to_datetime(col).strftime('%Y년'))
                    except Exception:
                        formatted_cols.append(str(col))
                df_fin.columns = formatted_cols
                df_fin = df_fin.rename(index=FINANCIALS_KR)
                return df_fin.T
        except Exception:
            continue
            
    return pd.DataFrame()
