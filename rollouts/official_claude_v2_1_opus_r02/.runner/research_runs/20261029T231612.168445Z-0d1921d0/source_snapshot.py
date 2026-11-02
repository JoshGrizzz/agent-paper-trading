
import yfinance as yf
t=['SPY','QQQ','XLE','MSFT','GOOGL','META','AMZN','NVDA','SMH','AAPL','IWM','INTC']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2)); print(c.between_time('15:59','16:00').iloc[-1].round(2))
