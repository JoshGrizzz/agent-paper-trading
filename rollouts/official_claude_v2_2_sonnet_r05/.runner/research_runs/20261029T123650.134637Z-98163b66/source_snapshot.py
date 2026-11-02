
import yfinance as yf
d=yf.download(['SPY','QQQ','XLE','XLV'],period='1d',interval='1m',prepost=True,progress=False,auto_adjust=False)
print(d['Close'].dropna().tail(3))
