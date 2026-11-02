
import yfinance as yf
t=['SPY','QQQ','XLE','TLT','MSFT','GOOGL','SMH','USO']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2)); print('low',d['Low'].min().round(2)); print('high',d['High'].max().round(2))
