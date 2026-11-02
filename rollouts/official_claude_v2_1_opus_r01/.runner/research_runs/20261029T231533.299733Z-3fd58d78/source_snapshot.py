
import yfinance as yf
t=['SPY','QQQ','SMH','MSFT','GOOGL','NVDA','AVGO','AAPL','AMZN','META']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill()
print(c.iloc[-1].round(2).to_string()); print(c.index[-1])
r=yf.download(t,period='2d',interval='1m',prepost=False,auto_adjust=False,progress=False)['Close'].ffill()
print(r.iloc[-1].round(2).to_string())
