
import yfinance as yf
t=['SPY','XLV','XLE','GLD','SMH','AAPL','QQQ','LLY','NVDA']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False,threads=False)
c=d['Close'];v=d['Volume']
for s in t:
  x=c[s].dropna()
  print(s, x.index[-1], round(x.iloc[-1],2), 'vol_last30', int(v[s].dropna().iloc[-30:].sum()))
