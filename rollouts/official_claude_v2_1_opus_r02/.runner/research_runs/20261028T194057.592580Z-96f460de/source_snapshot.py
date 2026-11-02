
import yfinance as yf
t=['SPY','QQQ','XLE','TLT','MSFT','GOOGL','SMH','USO','GLD','IWM']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); print(c.index[-1]); print(c.iloc[-1].round(2))
print(c.between_time('13:55','15:40').iloc[::10][['SPY','QQQ','TLT']].round(2))
