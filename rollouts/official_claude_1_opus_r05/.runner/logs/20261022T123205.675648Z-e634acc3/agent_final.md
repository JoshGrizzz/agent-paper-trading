## 2026-10-22T08:32:05.664075-04:00

### 本轮判断

- 市场与关键信息：今天盘前明显转弱。纳指 100 期货约 -1.9%，标普期货约 -1.1%，道指期货约 -0.7%。主要原因是市场对 AI 资本开支回报的担忧再起：META 把 2026 年资本开支下限上调到 $135B；TSLA 下调资本开支，盘前约 -5%；LRCX 盘前跌超 7%；INTC、MRVL、AMD 跌超 4%。伊朗局势升级：特朗普表示美国不与德黑兰谈判，沙特遭无人机袭击，Brent 升破 $112，WTI 接近 $100。10 年期美债收益率约 5.15%（+3bp）。盘前报价：QQQ 约 714.01（较昨收 725.20 跌 1.54%），SMH 约 538.36（较昨收 556.70 跌 3.29%）。broker 中的估值价格仍是 stale 的旧价，账户净值约 100,341.65，实际应低于此值。来源：[Yahoo：Nasdaq Futures Slide Premarket](https://finance.yahoo.com/markets/stocks/articles/nasdaq-futures-slide-premarket-ai-111659890.html)、[Yahoo：Why Are Nasdaq Futures Falling](https://finance.yahoo.com/markets/stocks/articles/why-nasdaq-futures-falling-premarket-085201550.html)、[Sunday Guardian 道指期货](https://sundayguardianlive.com/business/dow-jones-futures-today-trading-lower-056-to-068-amid-multi-day-tech-led-rally-major-corporate-earnings-escalating-geopolitical-tensions-check-key-drivers-what-investors-must-know-310203)、Yahoo 报价页（QQQ/SMH）。
- 当前策略及主要理由：适度降低科技和半导体敞口，暂不全面撤退。持仓中科技 beta 偏高（QQQ 约 40%、SMH 约 17%），AI 资本开支担忧、油价冲击、美债收益率上行和下周 FOMC 叠加，下行风险加大。计划卖出一半 SMH（15 股，限价 536，低于盘前价，大概率可以立即成交）。QQQ 卖出 10 股，限价 716.50，略高于盘前价，等反弹时成交。保留 SPY、其余 QQQ/SMH 和 XLE；XLE 受益于油价上涨，可以对冲。
- 主要风险：跳空低开后在低位卖出，如果盘中 V 型反弹会错过回升；如果抛售加剧，剩余科技仓位仍会继续亏损。

### 资金与持仓检查

- `cash.available`：2534.6000
- 主方案买入资金需求：0.00（只有卖单）
- Backup 1 买入资金需求：0.00（只有卖单）
- Backup 2 买入资金需求：未提供，0.00
- 预计冻结现金：0.00（broker 返回冻结现金 0）
- 卖出数量检查：主方案卖出 SMH 15 股，不超过 available_quantity 30；卖出 QQQ 10 股，不超过 55。Backup 1 卖出 SMH 15 股，不超过 30。broker 冻结股份 QQQ 10、SMH 15（跨候选取最大值）

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000003
  - 有效时间：2026-10-22T08:33:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：ok=true，状态 pending。提交后 status 确认方案在 open_plans 中，冻结股份 QQQ 10、SMH 15。尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：SMH
      - 数量：15
      - 限价：536.00
      - 订单 ID：ord_000009
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：10
      - 限价：716.50
      - 订单 ID：ord_000010

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SMH
      - 数量：15
      - 限价：528.00
      - 订单 ID：ord_000011

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：12:00 结算后，确认 SMH/QQQ 卖单是否成交及成交价。观察盘中能否从低开中修复、油价和伊朗局势、美债收益率，以及 8:30 公布的初请数据。卖出得到的现金（约 8k–15k）可考虑加到 XLE 或 GLD，或者等科技股企稳后再买回。
- 改变当前判断的条件：盘中收复大部分跌幅、AI 股企稳，则考虑把 SMH/QQQ 买回；抛售加剧（QQQ 跌超 2.5%）或中东冲突升级，则进一步减仓 QQQ/SPY，提高现金或能源仓位；油价急跌，则重新评估 XLE。