
import yfinance as yf
t=['SPY','QQQ','SMH','MSFT','NVDA','AVGO','AMZN','MU','AAPL','IWM']
d=yf.download(t,period='1d',interval='1m',prepost=False,auto_adjust=False,progress=False)
c=d['Close'].ffill()
print(c.iloc[-1].round(2).to_string()); print(d['Low'].min().round(2).to_string()); print(d['High'].max().round(2).to_string()); print(c.index[-1])
