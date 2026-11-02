
import yfinance as yf
t=['SPY','QQQ','SMH','GOOGL','XLE','NVDA','AAPL','^VIX','SQQQ','AMZN']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
for s in t:
    c=d['Close'][s].dropna(); l=d['Low'][s].dropna(); h=d['High'][s].dropna()
    print(s, round(c.iloc[-1],2), c.index[-1].strftime('%H:%M'),'lo',round(l.min(),2),'hi',round(h.max(),2))
