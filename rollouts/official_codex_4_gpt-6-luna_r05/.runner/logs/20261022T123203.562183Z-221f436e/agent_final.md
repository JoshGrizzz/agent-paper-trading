## 2026-10-22T08:32:03.549110-04:00

### 本轮判断

- 市场与关键信息：盘前 TQQQ 报约 $69.27，较前收跌约 4.6%；Reuters 报导纳指期货跌逾 1%，AI 支出担忧加剧。[盘前报价](https://stockmarketwatch.com/stock/TQQQ/premarket) [Reuters](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-ai-worries-resurface-oil-climbs-ce785cd9d08ff525)
- 当前策略及主要理由：对几乎全仓的 3 倍纳指 ETF 设置全仓卖出限价阶梯，降低市场继续下跌时的风险。
- 主要风险：盘前报价与 broker 最新估值不同；限价单可能不成交，杠杆 ETF 价格也可能迅速反弹或下跌。

### 资金与持仓检查

- `cash.available`：$64.14。
- 主方案买入资金需求：$0.00。
- Backup 1 买入资金需求：$0.00。
- Backup 2 买入资金需求：$0.00。
- 预计冻结现金：$0.00；broker 冻结 TQQQ 股份 1,394 股。
- 卖出数量检查：主方案、Backup 1、Backup 2 各卖出 TQQQ 1,394 股，均不超过提交前 `available_quantity` 1,394 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000002`
  - 有效时间：2026-10-22 08:34:00 至 12:00:00（美东时间）
  - broker 整体结果：`ok: true`，状态 pending；复核后仍 pending，未成交。
  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：1,394
      - 限价：$69.00
      - 订单 ID：`ord_000003`
  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：无
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：1,394
      - 限价：$68.00
      - 订单 ID：`ord_000004`
  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：无
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：1,394
      - 限价：$67.00
      - 订单 ID：`ord_000005`

### 后续计划

- 下轮重点检查：方案选择、成交记录、持仓及可用现金。
- 改变当前判断的条件：若方案到期未成交，结合届时 broker 的新鲜估值和市场状况重新评估。