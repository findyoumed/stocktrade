import numpy as np
import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

# [LOG: 20260604_1147]
# 삼성전자 주식 데이터 불러오기
df = stock.get_market_ohlcv_by_date("20250101", "20260531", "005930")

# 특성과 타겟 설정 (전날까지의 데이터로 다음 날의 고가 예측)
X = df[['시가', '저가', '종가', '거래량']].shift(1).iloc[1:]
y = df['고가'].iloc[1:]

# [LOG: 20260604_1203]
# 학습 및 테스트 데이터 분할 (학습 범위를 대폭 늘리고 마지막 2주만 예측하여 매일 변하는 빨간선 복원)
X_train, X_test = X[:'20260515'], X['20260516':'20260531']
y_train, y_test = y[:'20260515'], y['20260516':'20260531']

# 랜덤 포레스트 모델 학습
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 예측
predictions = model.predict(X_test)

# 결과 시각화
plt.figure(figsize=(14, 7))
plt.plot(df.index, df['고가'], label='Actual High Price', color='blue')
plt.plot(X_test.index, predictions, label='Predicted High Price', color='red', linestyle='--')
plt.title('Samsung Electronics Stock Price Prediction')
plt.xlabel('Date')
plt.ylabel('High Price')
plt.legend()
plt.show()