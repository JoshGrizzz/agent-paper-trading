
import yfinance as yf
t=['SPY','QQQ','IWM','SMH','TLT','GLD','USO','UUP','VXX','XLE','XLF','XLK','XLV','XLU','XLP','IBIT','NVDA','MSFT','GOOGL','META','AAPL','AMZN','TSLA','AVGO','MU']
d=yf.download(t,period='3mo',interval='1d',auto_adjust=False,progress=False)['Close']
r=d.iloc[-1]
print(d.index[-1])
for s in t:
  c=d[s].dropna()
  print(s, round(c.iloc[-1],2), '1d%.1f 5d%.1f 1m%.1f 3m%.1f'%(100*(c.iloc[-1]/c.iloc[-2]-1),100*(c.iloc[-1]/c.iloc[-6]-1),100*(c.iloc[-1]/c.iloc[-22]-1),100*(c.iloc[-1]/c.iloc[0]-1)))
