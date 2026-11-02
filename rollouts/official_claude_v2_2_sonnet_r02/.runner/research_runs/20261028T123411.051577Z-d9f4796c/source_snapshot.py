
import yfinance as yf
for t in ['SPY','QQQ','VTI']:
    h=yf.Ticker(t).history(period='2d',interval='1m',prepost=True)
    print(t,h.tail(2)[['Open','Close']].to_string())
