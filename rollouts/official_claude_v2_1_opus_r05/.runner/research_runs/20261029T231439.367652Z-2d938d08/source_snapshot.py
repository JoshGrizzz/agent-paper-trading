
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','GOOGL','AMZN','AAPL','MSFT','NVDA','META']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(d.index[-1]); print(c.iloc[-1].round(2).to_string())
