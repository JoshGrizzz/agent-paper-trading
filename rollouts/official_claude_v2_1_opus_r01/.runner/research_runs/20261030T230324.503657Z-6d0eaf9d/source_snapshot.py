
import yfinance as yf
t=['SPY','QQQ','SMH','MSFT','NVDA','AAPL','AMZN']
m=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=m['Close'].ffill()
print(c.iloc[-1].round(2).to_string()); print(m.index[-1])
print(c.between_time('15:30','16:00').iloc[[0,-1]].round(2).to_string())
