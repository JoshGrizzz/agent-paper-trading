
import yfinance as yf
t=['SPY','QQQ','SMH','IWM','XLE','XLV','XLU','GLD','TLT','NVDA','MSFT','META','AAPL','AMZN','GOOGL','VXX','XLP','USO']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill();print(c.index[-1])
for s in t:
  x=c[s];print(s,round(x.iloc[-1],2),'hi',round(d['High'][s].max(),2),'lo',round(d['Low'][s].min(),2),'open',round(d['Open'][s].dropna().iloc[0],2))
