
import yfinance as yf
t=['SPY','QQQ','SMH','SOXL','TQQQ','NVDA','AVGO','MU','AMD','IWM','RSP','GOOGL','MSFT','XLE','GLD','TSM','UPRO']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); v=d['Volume']
print(c.tail(3).round(2).T.to_string()); print(v.sum().to_string())
