
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','^TNX','CL=F']
d=yf.download(t,period='1d',interval='15m',prepost=False,auto_adjust=False,progress=False,threads=False)['Close']
print(d.dropna(how='all').round(2).to_string())
