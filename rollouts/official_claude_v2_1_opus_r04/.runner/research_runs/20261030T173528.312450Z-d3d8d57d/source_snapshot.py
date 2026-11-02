
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','XLV','IWM','^VIX']
d=yf.download(t,period='1d',interval='15m',auto_adjust=False,progress=False,threads=False)
print(d['Close'].round(2).to_string())
