
import yfinance as yf
t=['SPY','QQQ','XLE','MSFT','GOOGL','META','AMZN','NVDA','SMH','AAPL','IWM','INTC','TLT','XLV','XLU','GLD','USO']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2))
