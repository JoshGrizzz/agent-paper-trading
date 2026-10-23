## 2026-10-22T08:37:05.543074-04:00

### 本轮判断

- 市场与关键信息：
  - 盘前全面避险：纳指 100 期货约 -1.6%~-1.9%，S&P 期货约 -0.9%~-1.1%，道指期货约 -0.6%。
  - 原因有两条。
    - 一是市场重新担心 AI 资本开支能不能回本：META 上调资本开支下限后转跌；TSLA 下调资本开支，盘前约 -5%；LRCX 盘前跌超 7%；INTC、MRVL、AMD 跌超 4%。
    - 二是油价急升：Brent 超过 112 美元，WTI 接近 100 美元。起因是特朗普称不与伊朗谈判，NYT 报道美以拟在中期选举后对伊朗再度打击，沙特油田还遭到无人机袭击。
  - 盘前报价：QQQ 714.47（10/21 收盘 725.20），SMH 538.85（10/21 收盘 556.70，约 -3.2%），SPY 766.38（收盘 773.09），XLE 68.75（收盘 68.16，+0.85%）。
  - 今天公布初请失业金人数，美联储 10/28 公布议息结果。
  - 来源：[Stocktwits](https://stocktwits.com/news-articles/markets/equity/nasdaq-futures-slide-premarket-as-ai-spending-worries-resurface-oil-tops-112-on-iran-tensions-supply-concerns/cZxw43bRBwp)、[CNBC](https://www.cnbc.com/2026/10/21/stock-market-today-live-updates.html)、[Yahoo QQQ](https://finance.yahoo.com/quote/QQQ/)、[Yahoo SMH](https://finance.yahoo.com/quote/SMH/)
- 当前策略及主要理由：降低科技和半导体敞口，增加能源对冲，但不在跳空低点恐慌卖出。
  - SMH 挂 545 卖出 10 股（比盘前高约 1.1%）。
  - QQQ 挂 721 卖出 10 股（约成本价，比盘前高约 0.9%）。
  - 用剩余现金按 69.00 买入 XLE 100 股。XLE 是油价和地缘风险的对冲，同时受益于当前的油价趋势。
- 主要风险：
  - 科技股继续单边下跌、不反弹，卖单无法成交，回撤扩大。
  - 局势突然缓和导致油价回落，XLE 追高被套。
  - 两个卖单只有部分成交，导致仓位调整不完整。

### 资金与持仓检查

- `cash.available`：7543.50（提交前）
- 主方案买入资金需求：100×69.00 = 6900.00
- Backup 1 买入资金需求：未提供（0.00）
- Backup 2 买入资金需求：未提供（0.00）
- 预计冻结现金：6900.00（broker 返回 reservation.cash = 6900.00，提交后 cash.available = 643.50）
- 卖出数量检查：
  - SMH 卖出 10，不超过 available_quantity 20；QQQ 卖出 10，不超过 available_quantity 40。
  - 两只均为 10/21 买入，今天卖出不受日内限制。XLE 本方案只买不卖。
  - broker 冻结 QQQ 10 股、SMH 10 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000003
  - 有效时间：2026-10-22T08:39:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：ok = true，status = pending

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：XLE
      - 数量：100
      - 限价：69.00
      - 订单 ID：ord_000010
    - 订单：
      - 操作：卖出
      - 标的：SMH
      - 数量：10
      - 限价：545.00
      - 订单 ID：ord_000011
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：10
      - 限价：721.00
      - 订单 ID：ord_000012

  - Backup 1：
    - broker 状态：未提供
    - 拒绝原因：不适用

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：
  - plan_000003 哪些订单成交、成交价多少。今天买入的 XLE 当天不能卖；今天卖出的 SMH、QQQ 当天不能买回。
  - Brent 和 WTI 油价走势、伊朗和沙特局势、初请失业金数据、10 年期美债收益率。
  - 半导体股的跌势是否扩大。
- 改变当前判断的条件：
  - 科技股收复盘前跌幅、Nasdaq 转涨：停止减仓，考虑回补。
  - 油价继续冲高、大盘跌超 2%：进一步把 SMH 和 QQQ 减到更低仓位，或者加仓 XLE。
  - 地缘局势出现缓和信号、油价回落：减持 XLE，转回宽基。