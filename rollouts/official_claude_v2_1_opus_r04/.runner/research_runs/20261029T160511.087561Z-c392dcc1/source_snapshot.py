
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','MSFT','GOOGL','NVDA','META','AMZN','AAPL','CL=F','^TNX']
d=yf.download(t,period='1d',interval='15m',prepost=False,auto_adjust=False,progress=False,threads=False)['Close']
print(d.dropna(how='all').between_time('09:30','12:00').round(2).to_string())
