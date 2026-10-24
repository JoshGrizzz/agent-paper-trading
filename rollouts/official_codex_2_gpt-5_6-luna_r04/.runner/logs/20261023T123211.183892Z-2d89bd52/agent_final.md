## 2026-10-23T08:32:11.172678-04:00

### 本轮判断

- 市场与关键信息：纳指期货小幅走低，SQQQ 前一日大涨约 8.55%，短线反弹风险较高。[AP](https://apnews.com/article/7b47ef3b037bfba4e34f685329b9b963) [Investing.com](https://www.investing.com/etfs/ultrapro-short-qqq-historical-data)
- 当前策略及主要理由：分层限价卖出全部 SQQQ，优先锁定反弹价格。
- 主要风险：市场继续下跌时可能仅以较低备选限价成交，或方案全部不成交。

### 资金与持仓检查

- `cash.available`：984.2000
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：三组均卖出 SQQQ 2100 股；提交前 `available_quantity=2100`，未超额。复核后冻结 2100 股，`available_quantity=0`。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000007`
  - 有效时间：2026-10-23T08:33:00-04:00 至 2026-10-23T12:00:00-04:00
  - broker 整体结果：`ok=true`，`pending`，`fills=[]`

  - 主方案：
    - broker 状态：accepted
    - 订单：卖出 SQQQ 2100 股，限价 39.80，订单 ID `ord_000019`

  - Backup 1：
    - broker 状态：accepted
    - 订单：卖出 SQQQ 2100 股，限价 39.50，订单 ID `ord_000020`

  - Backup 2：
    - broker 状态：accepted
    - 订单：卖出 SQQQ 2100 股，限价 39.20，订单 ID `ord_000021`

### 后续计划

- 下轮重点检查方案是否成交、实际成交价、现金及 SQQQ 持仓。
- 若未成交，将根据纳指趋势和 SQQQ 价格重新决定；若成交，优先保持现金并等待更明确机会。