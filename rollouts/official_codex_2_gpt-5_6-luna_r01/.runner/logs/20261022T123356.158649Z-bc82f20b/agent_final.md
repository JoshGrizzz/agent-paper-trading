## 2026-10-22T08:33:56.147176-04:00

### 本轮判断

- 市场与关键信息：今日纳指期货盘前约下跌 1.5%–1.8%，成长和半导体板块承压；SMCI 昨日收于约 35.55。[盘前市场](https://www.cannontrading.com/tools/daily-updates/uploads/briefing-oct22-2026-readers-web-v1.html) [SMCI收盘](https://chartexchange.com/symbol/nasdaq-smci/historical/)
- 当前策略及主要理由：利用新交易日解除日内限制，逢反弹退出高度集中的 SMCI 持仓。
- 主要风险：若 SMCI 持续下跌且未触及限价，方案可能暂不成交。

### 资金与持仓检查

- `cash.available`：1,665.7300
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：提交前 SMCI `available_quantity=2700`；主方案及两个 backup 各卖出 2700，均不超过可用持仓。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000002`
  - 有效时间：2026-10-22T08:35:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：accepted，pending；当前无成交；已冻结 SMCI 2700 股。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：SMCI
      - 数量：2700
      - 限价：36.50
      - 订单 ID：`ord_000004`

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SMCI
      - 数量：2700
      - 限价：35.50
      - 订单 ID：`ord_000005`

  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SMCI
      - 数量：2700
      - 限价：34.50
      - 订单 ID：`ord_000006`

### 后续计划

- 下轮重点检查：主方案或 backup 的成交情况、成交价格及现金释放。
- 改变当前判断的条件：SMCI 未成交且市场继续转弱时，优先保留较低限价退出机会。