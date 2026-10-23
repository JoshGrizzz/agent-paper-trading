## 2026-10-22T08:32:03.549097-04:00

### 本轮判断

- 市场与关键信息：[今早纳指期货下跌逾 1%](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-ai-worries-resurface-oil-climbs-ce785cd9d08ff525)，[Lam Research 财报后盘前走弱](https://www.marketscreener.com/news/ai-stocks-slide-after-earnings-disappoint-french-bonds-tumble-and-oil-tops-112-ce785cd9d089fe27)。broker 的 SOXL 估值仍停在昨天 11:59，已过期。
- 当前策略及主要理由：对 800 股 SOXL 设置互斥的分档卖出限价，优先争取较高价格，同时应对继续走弱。
- 主要风险：价格可能跌破所有限价，导致本轮未成交；目前没有可用于判断实时净值的新鲜 broker 估值。

### 资金与持仓检查

- 提交前 `cash.available`：$18,400.00
- 主方案买入资金需求：$0.00
- Backup 1 买入资金需求：$0.00
- Backup 2 买入资金需求：$0.00
- 预计冻结现金：$0.00；broker 确认冻结 SOXL 800 股。
- 卖出数量检查：每个候选分别卖出 SOXL 800 股，均不超过提交前 `available_quantity` 800 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000003`
  - 有效时间：2026-10-22T08:34:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：`ok: true`；复查时方案为 `pending`，尚无新增成交。
  - 主方案：`accepted`；卖出 SOXL 800 股，限价 $101.00，订单 `ord_000007`。
  - Backup 1：`accepted`；卖出 SOXL 800 股，限价 $95.00，订单 `ord_000008`。
  - Backup 2：`accepted`；卖出 SOXL 800 股，限价 $85.00，订单 `ord_000009`。

### 后续计划

- 下轮重点检查：broker 实际选中的候选、成交价、现金及持仓。
- 改变当前判断的条件：半导体行情企稳，或业绩后的卖压持续加重。