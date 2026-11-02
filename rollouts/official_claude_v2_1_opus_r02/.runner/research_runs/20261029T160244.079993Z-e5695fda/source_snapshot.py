
import yfinance as yf
t=['SPY','QQQ','XLE','MSFT','GOOGL','META','AMZN','NVDA','SMH','TLT','USO','AAPL','IWM']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2)); print('low',d['Low'].between_time('09:30','16:00').min().round(2))
