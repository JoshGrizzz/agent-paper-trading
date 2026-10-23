## 2026-10-22T08:37:46.929470-04:00

### 本轮判断

- 市场与关键信息：Reuters 报道纳指期货跌逾 1%，市场消化 Tesla 与 Meta 业绩并担忧 AI 支出。[Reuters/MarketScreener](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-ai-worries-resurface-oil-climbs-ce785cd9d08ff525) Tesla 盘后下跌，Meta 收入超预期。[AP：Tesla](https://apnews.com/article/cfe0453f6bf0d08d22150022128492fa) [AP：Meta](https://apnews.com/article/13ecd6c459e39a3602f302bcc2412fe9)
- 当前策略及主要理由：分层限价减持 TQQQ，以降低对 3 倍杠杆 Nasdaq 的集中暴露；较低限价的备选方案在主方案未成交时生效。
- 主要风险：当前 broker 估值仍使用昨日 15:29 的价格；盘前波动可能使订单无法成交或以较低价格成交。

### 资金与持仓检查

- `cash.available`：$29.50。
- 主方案买入资金需求：$0.00（无买单）。
- Backup 1 买入资金需求：$0.00（无买单）。
- Backup 2 买入资金需求：$0.00（无买单）。
- 预计冻结现金：$0.00。
- 卖出数量检查：提交前 `available_quantity` 为 1,402 股；主方案卖出 700 股、Backup 1 卖出 700 股、Backup 2 卖出 1,402 股，各候选均未超过可用数量。

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000003
  - 有效时间：2026-10-22 08:39 至 12:00（美东时间）
  - broker 整体结果：`ok: true`，方案 `pending`；冻结现金 $0，冻结 TQQQ 1,402 股。
  - 主方案：
    - broker 状态：accepted
    - 订单：卖出 TQQQ 700 股，限价 $68.50，订单 ID ord_000007
  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：卖出 TQQQ 700 股，限价 $67.00，订单 ID ord_000008
  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：卖出 TQQQ 1,402 股，限价 $66.00，订单 ID ord_000009
  - 状态复查：主方案和两个 backup 均 accepted；方案待结算，尚无成交。`positions[].available_quantity` 当前为 0，因为整套候选方案冻结了 1,402 股。

### 后续计划

- 下轮重点检查：方案选择、成交和更新后的 TQQQ 估值。
- 改变当前判断的条件：若卖出方案未成交且 Nasdaq 恢复走强，重新评估减持幅度。