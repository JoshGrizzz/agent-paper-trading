
import yfinance as yf
t=['SPY','QQQ','XLE','XLV','AMZN','NVDA','SMH','AAPL','IWM','INTC','TLT','XLU','GLD','MSFT','GOOGL']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2))
r=d.between_time('09:30','16:00'); print('low',r['Low'].min().round(2)); print('high',r['High'].max().round(2))
