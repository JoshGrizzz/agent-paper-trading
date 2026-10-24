## 2026-10-23T15:34:58.264426-04:00

### 本轮判断

- 市场与关键信息：午后纳指反弹不稳，AI成本与融资担忧仍在；META继续弱于大盘。[Reuters市场报道](https://www.investing.com/news/economy-news/asian-shares-wobble-as-tech-rout-boosts-bonds-dents-rate-hike-bets-4709754)
- 当前策略及主要理由：减半META仓位，保留PSQ对冲及现金。
- 主要风险：META若快速反弹，减仓会损失上行；PSQ今日买入，暂受日内卖出限制。

### 资金与持仓检查

- `cash.available`：`19420.0700`
- 主方案买入资金需求：`0.00`
- Backup 1买入资金需求：`0.00`
- Backup 2买入资金需求：`0.00`
- 预计冻结现金：`0.00`
- 卖出数量检查：主方案50股、Backup 1为50股、Backup 2为100股，均不超过提交前META `available_quantity=100`。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000009`
  - 有效时间：`2026-10-23T15:36:00-04:00`至`2026-10-23T19:00:00-04:00`
  - broker整体结果：`ok=true`，方案`pending`；冻结现金`0`，META冻结100股

  - 主方案：
    - broker状态：accepted
    - 订单：卖出META，数量50，限价`645.00`，订单ID：`ord_000022`

  - Backup 1：
    - broker状态：accepted
    - 订单：卖出META，数量50，限价`643.00`，订单ID：`ord_000023`

  - Backup 2：
    - broker状态：accepted
    - 订单：卖出META，数量100，限价`640.00`，订单ID：`ord_000024`

- 撤销交易方案：不适用。

### 后续计划

- 下轮重点检查：plan_000009选中的候选、META实际成交数量及现金变化。
- 改变当前判断的条件：若META明显反弹且方案未成交，则保留剩余仓位；若继续走弱，则执行更低限价的减仓方案。