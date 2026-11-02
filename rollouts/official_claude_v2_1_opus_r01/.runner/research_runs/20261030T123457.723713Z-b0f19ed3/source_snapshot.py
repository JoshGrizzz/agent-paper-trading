
import yfinance as yf
t=['SPY','QQQ','SMH','MSFT','NVDA','AVGO','AMZN','INTC','AAPL','MU']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill()
print(c.iloc[-1].round(2).to_string()); print(c.index[-1])
