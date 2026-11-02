
import yfinance as yf
t=['SMH','SOXX','META','AMZN','AAPL','XLU','CEG','VST','ANET','AMD','LRCX','SNDK','WDC','STX','IWM','XLF','GEV','XLI','XLV']
d=yf.download(t,period='6mo',interval='1d',auto_adjust=False,progress=False,threads=False)['Close']
for s in t:
  if s not in d: continue
  c=d[s].dropna()
  if len(c)<64: print(s,'nodata'); continue
  print(s, round(c.iloc[-1],2), '1w%',round((c.iloc[-1]/c.iloc[-6]-1)*100,1),'1m%',round((c.iloc[-1]/c.iloc[-22]-1)*100,1),'3m%',round((c.iloc[-1]/c.iloc[-64]-1)*100,1),'6m%',round((c.iloc[-1]/c.iloc[0]-1)*100,1), 'off_hi%', round((c.iloc[-1]/c.max()-1)*100,1))
