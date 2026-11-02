
import yfinance as yf
for t in ['SPY','QQQ','VIX' if False else 'VXX']:
    h=yf.Ticker(t).history(period='3d',interval='15m',prepost=False)
    print(t);print(h.tail(8)[['Open','High','Low','Close']].to_string())
