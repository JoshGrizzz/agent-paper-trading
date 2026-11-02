
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','MSFT','GOOGL','NVDA','AMZN','AAPL','META','MU','TSM','^TNX','CL=F']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(d.index[-1]); print(c.iloc[-1].round(2).to_string())
