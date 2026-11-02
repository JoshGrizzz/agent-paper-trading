
import yfinance as yf
t=['SPY','QQQ','SMH','IWM','XLE','XLV','XLU','GLD','TLT','NVDA','AAPL','AMZN','VXX','USO']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill();print(c.index[-1])
for s in t:
  x=c[s];r=x[x.index.strftime('%H:%M')<='15:59'];print(s,'close',round(r.iloc[-1],2),'last',round(x.iloc[-1],2),'lo',round(d['Low'][s].min(),2))
