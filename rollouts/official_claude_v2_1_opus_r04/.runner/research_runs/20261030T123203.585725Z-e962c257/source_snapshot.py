
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','NVDA','AVGO','MU','AMZN','INTC','AAPL','META','CL=F','^TNX']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False,threads=False)['Close']
print(d.ffill().iloc[-1].round(2).to_string())
