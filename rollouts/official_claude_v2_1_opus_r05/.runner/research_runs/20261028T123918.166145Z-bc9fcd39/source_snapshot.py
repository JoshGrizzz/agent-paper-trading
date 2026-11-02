
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','GLD','NVDA','MU','AVGO','TSM','IWM','MSFT','GOOGL','VRT','GEV','XLU','ANET','SOXX']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill().iloc[-1]; v=d['Volume'].sum()
print(d.index[-1]); print(c.round(2).to_string()); print(v.to_string())
