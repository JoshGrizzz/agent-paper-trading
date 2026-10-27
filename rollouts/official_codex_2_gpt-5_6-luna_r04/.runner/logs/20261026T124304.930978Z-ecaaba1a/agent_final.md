## 2026-10-26T08:43:04.896586-04:00

### 本轮判断

- 市场与关键信息：纳指期货小幅上涨，但本周有密集财报与美联储决议，AI 交易仍具不确定性。[AP](https://apnews.com/article/be3a56f58a77c5be863f0289d280be92) [Reuters](https://www.investing.com/news/economy-news/us-stock-futures-edge-up-as-oil-falls-heading-into-earnings-barrage-4971878)
- 当前策略及主要理由：分层限价卖出全部 TQQQ，优先在接近成本处退出周末遗留的高杠杆仓位。
- 主要风险：盘前成交量门槛或价格条件可能导致方案不成交，TQQQ 仍可能继续波动。

### 资金与持仓检查

- `cash.available`：856.2000
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：三组均卖出 TQQQ 1250 股；提交前 `available_quantity=1250`，未超额。复核后冻结 1250 股，`available_quantity=0`。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000009`
  - 有效时间：2026-10-26T08:44:00-04:00 至 2026-10-26T12:00:00-04:00
  - broker 整体结果：`ok=true`，`pending`，`fills=[]`

  - 主方案：
    - broker 状态：accepted
    - 订单：卖出 TQQQ 1250 股，限价 67.40，订单 ID `ord_000024`

  - Backup 1：
    - broker 状态：accepted
    - 订单：卖出 TQQQ 1250 股，限价 67.00，订单 ID `ord_000025`

  - Backup 2：
    - broker 状态：accepted
    - 订单：卖出 TQQQ 1250 股，限价 66.50，订单 ID `ord_000026`

### 后续计划

- 下轮重点检查方案是否成交、实际成交价、现金和 TQQQ 持仓。
- 若未成交，将根据常规时段价格重新调整退出限价；若成交，保留现金等待财报与美联储事件明朗。