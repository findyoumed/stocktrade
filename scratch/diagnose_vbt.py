with open(r"d:\work\stocktrade\chapter3\backtest_engine.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
pattern = r"def run_vbt_backtest[\s\S]+?return vbt_df"
match = re.search(pattern, content)
if match:
    print("Found match in file:")
    print(repr(match.group(0)[:200]))
    print("...")
    print(repr(match.group(0)[-200:]))
    
    # Let's compare line by line
    orig_lines = [
        "def run_vbt_backtest(df, K, initial_budget, fee_rate_pct, slippage_rate_pct, use_drip=False):",
        '    """변동성 돌파 전략 백테스트를 수행합니다."""',
        "    # [LOG: 20260605_0950]",
        "    cost_rate = (fee_rate_pct + slippage_rate_pct) / 100",
        "    ",
        "    vbt_df = df.copy()",
        "    ",
        "    # OHLC 데이터 검증 (고가와 저가가 95% 이상 같은지 체크하여 종가만 채워진 부실 데이터 판별)",
        "    is_invalid_ohlc = (vbt_df['고가'] == vbt_df['저가']).mean() > 0.95",
        "    if is_invalid_ohlc:",
        '        st.session_state[\'vbt_warning\'] = "⚠️ 경고: 현재 종목 데이터는 시가/고가/저가가 누락되어 종가로 채워진 \'간소화/변형 버전\' 데이터입니다. 래리 윌리엄스의 변동성 돌파 전략이 정상적으로 작동하지 않을 수 있습니다."',
        "    else:",
        "        st.session_state['vbt_warning'] = None",
        "        ",
        "    vbt_df['Range'] = vbt_df['고가'].shift(1) - vbt_df['저가'].shift(1)",
        "    vbt_df['Buy_Target'] = vbt_df['시가'] + (vbt_df['Range'] * K)",
        "    vbt_df['Buy_Signal'] = vbt_df['고가'] > vbt_df['Buy_Target']",
        "    ",
        "    # 실제 매수 체결 가격 계산 (당일 시가 > 목표가인 갭상승의 경우 시가에 체결)",
        "    vbt_df['Buy_Price'] = np.where(",
        "        vbt_df['시가'] > vbt_df['Buy_Target'],",
        "        vbt_df['시가'],",
        "        vbt_df['Buy_Target']",
        "    )",
        "    ",
        "    # [LOG: 20260605_1020] 배당금 재투자 (DRIP) 반영 조건 설정",
        "    if use_drip and '배당금' in vbt_df.columns:",
        "        div_yield = vbt_df['배당금'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])",
        "        strategy_div_yield = np.where(vbt_df['Buy_Signal'], div_yield, 0.0)",
        "    else:",
        "        div_yield = 0.0",
        "        strategy_div_yield = 0.0",
        "        ",
        "    vbt_df['Strategy_Return'] = np.where(",
        "        vbt_df['Buy_Signal'],",
        "        (vbt_df['종가'] * (1 - cost_rate - 0.18 / 100)) / (vbt_df['Buy_Price'] * (1 + cost_rate)) + strategy_div_yield,",
        "        1.0",
        "    )",
        "    ",
        "    hold_returns = (vbt_df['종가'] / vbt_df['종가'].shift(1).fillna(vbt_df['종가'])) + div_yield",
        "    hold_returns_array = hold_returns.fillna(1.0).values",
        "    if len(hold_returns_array) > 0:",
        "        hold_returns_array[0] = hold_returns_array[0] - cost_rate",
        "    vbt_df['Hold_Return'] = hold_returns_array",
        "    ",
        "    vbt_df['Strategy_Cum_Return'] = (vbt_df['Strategy_Return'].cumprod() - 1) * 100",
        "    vbt_df['Hold_Cum_Return'] = (vbt_df['Hold_Return'].cumprod() - 1) * 100",
        "    ",
        "    vbt_df['Strategy_Balance'] = initial_budget * vbt_df['Strategy_Return'].cumprod()",
        "    vbt_df['Hold_Balance'] = initial_budget * vbt_df['Hold_Return'].cumprod()",
        "    vbt_df['Daily_Return_Pct'] = (vbt_df['Strategy_Return'] - 1) * 100",
        "    ",
        "    return vbt_df"
    ]
    
    file_lines = match.group(0).split("\n")
    print(f"Orig lines count: {len(orig_lines)}, File lines count: {len(file_lines)}")
    for idx, (ol, fl) in enumerate(zip(orig_lines, file_lines)):
        ol_clean = ol.strip()
        fl_clean = fl.strip()
        if ol_clean != fl_clean:
            print(f"Mismatch at line {idx+1}:")
            print("Expected:", repr(ol_clean))
            print("Found:   ", repr(fl_clean))
            break
else:
    print("Could not find vbt function in file via regex.")
