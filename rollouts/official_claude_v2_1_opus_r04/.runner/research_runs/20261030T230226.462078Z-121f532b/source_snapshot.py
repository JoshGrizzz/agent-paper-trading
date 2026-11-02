
import yfinance as yf
for s in ['SPY','SMH','QQQ','XLE','XLV','^VIX']:
    d=yf.Ticker(s).history(period='2d',interval='5m',prepost=True)
    r=d[d.index.date==d.index[-1].date()]
    print(s, 'last', round(d['Close'].iloc[-1],2), d.index[-1].strftime('%H:%M'), 'low', round(r['Low'].min(),2), 'high', round(r['High'].max(),2))
