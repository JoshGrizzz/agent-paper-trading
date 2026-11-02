
import yfinance as yf
t=['SPY','QQQ','SMH','XLV','XLE','MSFT','GOOGL','NVDA','META']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False,threads=False)['Close']
x=d.between_time('15:59','15:59')
print('close', x.round(2).to_string())
print('last', d.ffill().iloc[-1].round(2).to_string())
