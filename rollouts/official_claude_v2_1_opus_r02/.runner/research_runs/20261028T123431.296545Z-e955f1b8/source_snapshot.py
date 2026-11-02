
import yfinance as yf
t=['SPY','QQQ','SMH','NVDA','MSFT','GOOGL','META','AAPL','AMZN','TSLA','AVGO','MU','IWM','XLE','GLD']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill().iloc[-1]; print(d.index[-1]); print(c.round(2))
