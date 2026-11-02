## 2026-10-30T08:35:26.146816-04:00

### 本轮判断

- 市场与关键信息：纳指期货盘前下跌逾 2%；Amazon 业绩和展望不及预期，Intel 前景疲弱，加剧市场对 AI 投资支出的担忧。[美联社：市场与科技股](https://apnews.com/article/16c266731fdf64178f38070af2b42497)；[Reuters：纳指期货及 AI 投资担忧](https://www.marketscreener.com/news/nasdaq-futures-tumble-as-amazon-intel-results-deepen-ai-spending-woes-ce785fdbd880f125)
- 当前策略及主要理由：账户约七成权益为 QQQ。提交互斥限价卖出阶梯，最多减持 12 股，以降低集中度并保留大部分仓位。
- 主要风险：券商 QQQ 估值仍是前一日收盘价且标记 stale；若价格持续下跌、未回升至限价，卖单可能不成交。

### 资金与持仓检查

- `cash.available`：29539.2100。
- 主方案买入资金需求：0.00（无买单）。
- Backup 1 买入资金需求：0.00（无买单）。
- Backup 2 买入资金需求：0.00（无买单）。
- 预计冻结现金：0.00；broker 实际现金冻结为 0。
- 卖出数量检查：主方案、Backup 1、Backup 2 各卖出 QQQ 12 股，均不超过提交前 `available_quantity` 96 股；broker 冻结 QQQ 12 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000009
  - 有效时间：2026-10-30 08:37 至 12:00（美东时间）
  - broker 整体结果：`ok: true`，方案 pending；复查状态仍为 pending，尚无成交。
  - 主方案：
    - broker 状态：accepted
    - 订单：卖出 QQQ，数量 12，限价 708.00，订单 ID ord_000021
  - Backup 1：
    - broker 状态：accepted
    - 订单：卖出 QQQ，数量 12，限价 703.00，订单 ID ord_000022
  - Backup 2：
    - broker 状态：accepted
    - 订单：卖出 QQQ，数量 12，限价 698.00，订单 ID ord_000023

### 后续计划

- 下轮重点检查：方案选择与成交、QQQ 可用持仓和现金，以及盘中价格是否更新。
- 改变当前判断的条件：若科技股抛售继续扩大或 QQQ 风险集中度仍过高，再评估减仓；若价格企稳，则重新评估保留仓位的收益空间。