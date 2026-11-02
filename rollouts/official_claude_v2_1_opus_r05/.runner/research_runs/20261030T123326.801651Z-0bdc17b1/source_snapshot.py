
import yfinance as yf
t=['SPY','QQQ','SMH','XLE','GOOGL','AMZN','AAPL','MSFT','NVDA','INTC','AMD','TSM','MU','^TNX','CL=F']
d=yf.download(t,period='2d',interval='1m',prepost=True,auto_adjust=False,progress=False)
c=d['Close'].ffill(); i=d.index
y=i[(i.date==i[0].date())&(i.hour<16)][-1]
import pandas as pd
print(i[-1]); print(pd.DataFrame({'prevclose':c.loc[y],'last':c.iloc[-1],'chg%':(c.iloc[-1]/c.loc[y]-1)*100}).round(2))
