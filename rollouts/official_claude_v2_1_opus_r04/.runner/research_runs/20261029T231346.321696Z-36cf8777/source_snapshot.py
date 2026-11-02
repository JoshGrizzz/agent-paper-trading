
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','MSFT','GOOGL','NVDA','META','AMZN','AAPL']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False,threads=False)['Close']
print('close');print(d.between_time('15:59','15:59').round(2).T.to_string())
print('last');print(d.ffill().iloc[-1].round(2).to_string())
