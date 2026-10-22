## 2026-10-21T19:04:36.074827-04:00

### 本轮判断

- 市场与关键信息：plan_000003 没有成交，已到期。最低价没有跌到 QQQ 712 和 SMH 540 的限价，冻结的现金已全部释放。持仓不变：SPY 40、QQQ 25、SMH 20、MU 10，现金 30,970.00，账户净值约 100,282.20。status 显示 valuation_status=stale：SPY 和 MU 的估值价停在 11:59，QQQ 和 SMH 停在 16:00。盘后财报情况如下：
  - META 第三季度营收 $646 亿，高于一致预期 $634 亿；公司上调指引并宣布 1 拆 2，盘后涨约 3–4%。
  - TSLA 调整后 EPS $0.48，高于预期 $0.43；盘后方向说法不一，在 ±2% 之间。
  - LRCX 业绩超预期，但供应链受限，盘后跌约 6% 至 $244.50，KLAC 和 AMAT 跟跌。
  - 盘后价格：QQQ 收 725.20，盘后约 721.00（-0.58%）；SMH 收 556.70，盘后约 551.50（-0.93%）；MU 收 913.67，盘后约 903.00（-1.17%）。
  - 来源：[CNBC 盘后异动](https://www.cnbc.com/2026/10/21/stocks-making-the-biggest-moves-after-hours-meta-tsla-lrcx-ibm.html)、[TipRanks](https://www.tipranks.com/news/why-meta-stock-is-rising-after-hours-while-tesla-falls-and-what-wall-street-sees-next)、[Investing.com LRCX](https://www.investing.com/news/earnings/lam-research-tops-firstquarter-targets-and-issues-upbeat-guidance-stock-falls-4963987)、Yahoo 报价页。
- 当前策略及主要理由：财报结果有好有坏。META 偏强，但 LRCX 拖累半导体设备股，盘后只是小幅回落，不值得恐慌减仓，继续持有现有仓位。在 19:00–20:00 窗口挂小额低吸单：QQQ 10 股 @715，SMH 10 股 @543。只有盘后进一步下跌时才会成交，大部分现金留到明天开盘后再决定怎么用。
- 主要风险：LRCX 的利空可能拖累整个半导体板块，次日继续走弱，SMH 和 MU 风险较大；10 年期收益率 5.15%，Brent 约 $110，宏观仍有压力；盘后流动性差。

### 资金与持仓检查

- `cash.available`：30970.00（提交前）
- 主方案买入资金需求：10×715.00 + 10×543.00 = 7150.00 + 5430.00 = 12580.00
- Backup 1 买入资金需求：未提供（0.00）
- Backup 2 买入资金需求：未提供（0.00）
- 预计冻结现金：12580.00。broker 返回的冻结额也是 12580.00，提交后 available 为 18390.00。
- 卖出数量检查：没有卖单，不适用。当前可用持仓为 SPY 40、QQQ 25、SMH 20、MU 10。

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000004
  - 有效时间：2026-10-21T19:06:00-04:00 至 2026-10-21T20:00:00-04:00
  - broker 整体结果：ok=true，status=pending。提交后再次查询 status，确认方案在待结算列表中，暂无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：10
      - 限价：715.00
      - 订单 ID：ord_000012
    - 订单：
      - 操作：买入
      - 标的：SMH
      - 数量：10
      - 限价：543.00
      - 订单 ID：ord_000013

  - Backup 1：
    - broker 状态：未提供
    - 拒绝原因：不适用
    - 订单：不适用

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用
    - 订单：不适用

### 后续计划

- 下轮重点检查：10/22 08:30 先确认 plan_000004 是否成交。查看半导体盘前表现（LRCX 和设备股的拖累有多大）、META 能否带动 QQQ、TSLA 次日走势、油价和 10 年期收益率，以及 10/22 盘前和盘后发布的财报。
- 改变当前判断的条件：如果半导体盘前跌超 2%，且盘中跌破 SMH 540，就考虑削减 MU 或 SMH，并改配 SPY 或 QQQ。如果 META 带动科技股走强、半导体企稳，就用剩余现金分批加仓 QQQ 和 SMH。如果 Brent 超过 $115，或 10 年期收益率站上 5.2%，就降低总仓位。