
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','GLD','NVDA','MU','AVGO','TSM','IWM','XLF','GOOGL','MSFT','AMZN','META']
d=yf.download(t,period='3mo',interval='1d',auto_adjust=False,progress=False)['Close']
import pandas as pd
pd.set_option('display.width',250)
print(d.tail(8).round(2).T)
r=d.iloc[-1]/d.iloc[-21]-1; r3=d.iloc[-1]/d.iloc[0]-1
print(pd.DataFrame({'1m':r,'3m':r3}).round(3))
