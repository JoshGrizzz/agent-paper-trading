## 2026-10-30T08:35:26.146249-04:00

### 本轮判断

- 市场与关键信息：盘前 QQQ 约跌 2.5%，SQQQ 报 40.80 美元；Amazon 和 Intel 财报后科技股承压。[QQQ 报价](https://chartexchange.com/symbol/nasdaq-qqq/)；[SQQQ 报价](https://chartexchange.com/symbol/nasdaq-sqqq/)；[财报后市场报道](https://www.investing.com/news/stock-market-news/nasdaq-futures-tumble-as-amazon-intel-results-deepen-ai-spending-woes-4986163)
- 当前策略及主要理由：SQQQ 盘前报价高于 37.60 美元持仓成本，分档限价卖出，争取兑现涨幅。
- 主要风险：盘前价格可能迅速变化，成交须满足分钟成交量门槛；主方案可能仅成交一笔。broker 当前持仓估值仍为昨日价格，已过期。

### 资金与持仓检查

- `cash.available`：提交前 38,305.0250 美元；SQQQ `available_quantity` 为 1,500 股。
- 主方案买入资金需求：0.00 美元。
- Backup 1 买入资金需求：0.00 美元。
- Backup 2 买入资金需求：0.00 美元。
- 预计冻结现金：0.00 美元；broker 确认冻结 SQQQ 1,500 股。
- 卖出数量检查：主方案合计 750＋750＝1,500 股；两个 backup 各卖出 1,500 股，分别不超过提交前可用的 1,500 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000015`
  - 有效时间：2026-10-30T08:37:00-04:00 至 2026-10-30T12:00:00-04:00。
  - broker 整体结果：`ok: true`；复查时方案为 `pending`，尚无成交。
  - 主方案：`accepted`；卖出 SQQQ 750 股，限价 40.95 美元，订单 `ord_000044`；卖出 SQQQ 750 股，限价 41.85 美元，订单 `ord_000045`。
  - Backup 1：`accepted`；卖出 SQQQ 1,500 股，限价 40.15 美元，订单 `ord_000046`。
  - Backup 2：`accepted`；卖出 SQQQ 1,500 股，限价 38.50 美元，订单 `ord_000047`。

### 后续计划

- 下轮重点检查：broker 选中的候选、实际成交及剩余 SQQQ 持仓。
- 改变当前判断的条件：科技股继续大幅下跌，或开盘后出现明显反弹。