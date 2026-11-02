
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','^TNX','CL=F']
d=yf.download(t,period='1d',interval='5m',prepost=True,auto_adjust=False,progress=False,threads=False)['Close']
print(d.dropna(how='all').iloc[::6].round(2).to_string())
print(d.ffill().iloc[-1].round(2).to_string())
