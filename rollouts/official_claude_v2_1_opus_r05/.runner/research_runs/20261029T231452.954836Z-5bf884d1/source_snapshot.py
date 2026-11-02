
import yfinance as yf
t=['NVDA','AVGO','MU','TSM','AMD','KLAC','LRCX','AMAT','QCOM','ASML','INTC','MRVL','ARM','SMH','QQQ']
d=yf.download(t,period='1d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); i=d.index
close=c[i<=i[i.hour<16][-1]].iloc[-1]; last=c.iloc[-1]
import pandas as pd
print(pd.DataFrame({'close':close,'last':last,'chg%':(last/close-1)*100}).round(2))
