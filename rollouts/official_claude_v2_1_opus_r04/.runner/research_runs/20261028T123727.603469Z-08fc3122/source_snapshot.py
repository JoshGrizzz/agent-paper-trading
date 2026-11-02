
import yfinance as yf
t=['SPY','QQQ','SMH','NVDA','GOOGL','MSFT','XLE','GLD','AVGO','MU','VRT','GEV','IWM','TSM','META','AMZN','AAPL','SOXX','XLU','XLF','CEG','VST','ANET','AMD','LRCX','SNDK','WDC','STX']
d=yf.download(t,period='6mo',interval='1d',auto_adjust=False,progress=False)['Close']
last=d.iloc[-1]
for s in t:
  c=d[s].dropna()
  print(s, round(c.iloc[-1],2), '1w%',round((c.iloc[-1]/c.iloc[-6]-1)*100,1),'1m%',round((c.iloc[-1]/c.iloc[-22]-1)*100,1),'3m%',round((c.iloc[-1]/c.iloc[-64]-1)*100,1),'6m%',round((c.iloc[-1]/c.iloc[0]-1)*100,1), 'off_hi%', round((c.iloc[-1]/c.max()-1)*100,1))
