import sys
from pathlib import Path

engine_path = Path("chapter3/backtest_engine.py")
content = engine_path.read_text(encoding="utf-8")
content_lf = content.replace("\r\n", "\n")

# Target duplicate block: We search for the second run_sma_macd_filter_backtest definition.
# The first one starts around line 616. The second one starts around line 814.
first_def = content_lf.find("def run_sma_macd_filter_backtest")
second_def = content_lf.find("def run_sma_macd_filter_backtest", first_def + len("def run_sma_macd_filter_backtest"))

# Find where the duplicate block ends (just before def run_dca_backtest)
end_duplicate = content_lf.find("def run_dca_backtest")

if second_def == -1 or end_duplicate == -1:
    print("Error: Could not locate the duplicate block.")
    sys.exit(1)

duplicate_block = content_lf[second_def:end_duplicate]

new_functions = """def calculate_sharpe_ratio(returns_series):
    \"\"\"일간 수익률 시리즈를 기반으로 연율화된 샤프 지수(Sharpe Ratio)를 계산합니다.
    returns_series는 각 일자별 전략 수익률 비율(예: 1.01이면 +1% 수익)을 나타냅니다.
    \"\"\"
    if returns_series is None or len(returns_series) == 0:
        return 0.0
    daily_excess_returns = returns_series - 1.0
    mean_excess = daily_excess_returns.mean()
    std_excess = daily_excess_returns.std()
    
    # 분모가 0이 되는 경우 방지
    if std_excess > 1e-9:
        return float((mean_excess / std_excess) * np.sqrt(252))
    return 0.0


def extract_trades_to_df(df, strategy_choice, initial_budget, fee_rate_pct, slippage_rate_pct):
    \"\"\"각 백테스트 결과 데이터프레임을 분석하여 매수/매도 거래 이력 또는 DCA 적립 이력을 추출합니다.\"\"\"
    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100
    
    if strategy_choice == "적립식 존버 물타기 (DCA) 전략":
        purchases = []
        if 'Buy_Signal' in df.columns:
            shares = 0.0
            total_invested = 0.0
            for i, (idx, row) in enumerate(df.iterrows()):
                is_buy = row['Buy_Signal']
                price = row['종가']
                if i == 0:
                    # 최초 거치식 매수
                    injected = initial_budget
                    shares_bought = injected / (price * (1.0 + cost_rate))
                    shares += shares_bought
                    total_invested += injected
                    avg_price = price
                    purchases.append({
                        '적립일(매수일)': idx.strftime('%Y-%m-%d'),
                        '매수가격(종가)': f"{price:,.0f}원",
                        '추가 적립액': f"{injected:,.0f}원",
                        '매수 수량': f"{shares_bought:,.2f}주",
                        '누적 보유 수량': f"{shares:,.2f}주",
                        '평균 단가': f"{avg_price:,.0f}원"
                    })
                elif is_buy:
                    injected = row['Cash_Injected']
                    shares_bought = injected / (price * (1.0 + cost_rate))
                    shares += shares_bought
                    total_invested += injected
                    avg_price = total_invested / shares if shares > 0 else price
                    purchases.append({
                        '적립일(매수일)': idx.strftime('%Y-%m-%d'),
                        '매수가격(종가)': f"{price:,.0f}원",
                        '추가 적립액': f"{injected:,.0f}원",
                        '매수 수량': f"{shares_bought:,.2f}주",
                        '누적 보유 수량': f"{shares:,.2f}주",
                        '평균 단가': f"{avg_price:,.0f}원"
                    })
        return pd.DataFrame(purchases)
        
    elif strategy_choice == "변동성 돌파 전략 (Larry Williams)":
        trades = []
        if 'Buy_Signal' in df.columns and 'Buy_Price' in df.columns:
            for idx, row in df[df['Buy_Signal']].iterrows():
                buy_date = idx.strftime('%Y-%m-%d')
                buy_price = row['Buy_Price']
                sell_date = idx.strftime('%Y-%m-%d')
                sell_price = row['종가']
                ret_rate = (sell_price / buy_price - 1 - 2 * cost_rate) * 100
                
                idx_num = df.index.get_loc(idx)
                if idx_num > 0:
                    prev_balance = df['Strategy_Balance'].iloc[idx_num - 1]
                else:
                    prev_balance = initial_budget
                profit = df['Strategy_Balance'].iloc[idx_num] - prev_balance
                
                trades.append({
                    '매수일': buy_date,
                    '매수가격': f"{buy_price:,.0f}원",
                    '매도일': sell_date,
                    '매도가격': f"{sell_price:,.0f}원",
                    '수익액': f"{profit:+,.0f}원",
                    '수익률': f"{ret_rate:+.2f}%"
                })
        return pd.DataFrame(trades)
        
    # 일반 매매 전략 (추세 추종 및 보조 지표 등)
    pos_series = None
    if 'Position' in df.columns:
        pos_series = df['Position']
    elif 'Buy_Signal' in df.columns:
        pos_series = df['Buy_Signal']
    else:
        return pd.DataFrame()
        
    in_pos = pos_series.map(lambda x: True if x in [True, "ATTACK", 1, 1.0] else False)
    
    trades = []
    in_trade = False
    buy_date = None
    buy_price = 0.0
    buy_idx_loc = -1
    
    for i in range(len(df)):
        pos = in_pos.iloc[i]
        date = df.index[i]
        price = df['종가'].iloc[i]
        
        # 진입 (매수)
        if pos and not in_trade:
            in_trade = True
            buy_date = date
            buy_price = price
            buy_idx_loc = i
        # 청산 (매도)
        elif not pos and in_trade:
            in_trade = False
            sell_date = date
            sell_price = price
            
            ret_rate = (sell_price / buy_price - 1 - 2 * cost_rate) * 100
            if buy_idx_loc > 0:
                prev_balance = df['Strategy_Balance'].iloc[buy_idx_loc - 1]
            else:
                prev_balance = initial_budget
            profit = df['Strategy_Balance'].iloc[i] - prev_balance
            
            trades.append({
                '매수일': buy_date.strftime('%Y-%m-%d'),
                '매수가격': f"{buy_price:,.0f}원",
                '매도일': sell_date.strftime('%Y-%m-%d'),
                '매도가격': f"{sell_price:,.0f}원",
                '수익액': f"{profit:+,.0f}원",
                '수익률': f"{ret_rate:+.2f}%"
            })
            
    # 백테스트 종료일까지 포지션을 보유 중인 경우
    if in_trade:
        sell_date = df.index[-1]
        sell_price = df['종가'].iloc[-1]
        ret_rate = (sell_price / buy_price - 1 - cost_rate) * 100
        if buy_idx_loc > 0:
            prev_balance = df['Strategy_Balance'].iloc[buy_idx_loc - 1]
        else:
            prev_balance = initial_budget
        profit = df['Strategy_Balance'].iloc[-1] - prev_balance
        
        trades.append({
            '매수일': buy_date.strftime('%Y-%m-%d'),
            '매수가격': f"{buy_price:,.0f}원",
            '매도일': sell_date.strftime('%Y-%m-%d') + " (보유중)",
            '매도가격': f"{sell_price:,.0f}원",
            '수익액': f"{profit:+,.0f}원",
            '수익률': f"{ret_rate:+.2f}%"
        })
        
    return pd.DataFrame(trades)


"""

content_lf = content_lf.replace(duplicate_block, new_functions)
engine_path.write_text(content_lf, encoding="utf-8")
print("Successfully updated backtest_engine.py")
