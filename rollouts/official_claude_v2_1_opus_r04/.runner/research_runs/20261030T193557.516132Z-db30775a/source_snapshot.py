
import yfinance as yf
for s in ['SPY','SMH','QQQ']:
    d=yf.Ticker(s).history(period='1d',interval='1m',prepost=True)
    print(s, d['Close'].tail(3).round(2).to_dict(), 'dayLow', round(d['Low'].min(),2))
