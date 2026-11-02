
import yfinance as yf
t=['SPY','QQQ','SMH','GOOGL','XLE','NVDA','AMZN','AAPL','MSFT','META','^VIX','^TNX','CL=F','AVGO','TSM']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False)
for s in t:
    c=d['Close'][s].dropna(); l=d['Low'][s].dropna(); h=d['High'][s].dropna()
    td=c.index[-1].date()
    ct=c[c.index.date==td]; pc=c[c.index.date<td]
    print(s, round(ct.iloc[-1],2), c.index[-1].strftime('%H:%M'), 'prev', round(pc.iloc[-1],2) if len(pc) else None, 'lo',round(l[l.index.date==td].min(),2),'hi',round(h[h.index.date==td].max(),2))
