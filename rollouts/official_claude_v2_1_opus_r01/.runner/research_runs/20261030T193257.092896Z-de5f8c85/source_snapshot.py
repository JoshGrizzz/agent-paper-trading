
import yfinance as yf
t=['SPY','QQQ','SMH','MSFT','NVDA','AAPL','IWM','TLT','GLD','XLE']
d=yf.download(t,period='5d',interval='1d',auto_adjust=False,progress=False)
print(d['Close'].round(2).to_string())
m=yf.download(t,period='1d',interval='1m',prepost=False,auto_adjust=False,progress=False)
print(m['Close'].ffill().iloc[-1].round(2).to_string()); print(m['Low'].min().round(2).to_string()); print(m.index[-1])
