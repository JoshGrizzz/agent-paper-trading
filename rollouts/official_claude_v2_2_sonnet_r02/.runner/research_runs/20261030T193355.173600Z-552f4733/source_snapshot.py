
import yfinance as yf
for t in ['SPY','VXX']:
    h=yf.Ticker(t).history(period='2d',interval='5m',prepost=False)
    print(t);print(h.tail(6)[['Open','High','Low','Close']].to_string())
