
import yfinance as yf
d=yf.download(['SPY','QQQ','NVDA','MSFT'],period='5d',interval='1d',progress=False,auto_adjust=False)
print(d['Close'].tail(6))
