## 2026-10-22T08:33:56.150457-04:00

### 本轮判断

- 市场与关键信息：纳指期货下跌逾 1%；油轮在霍尔木兹海峡受损的报道推动油价上涨。Meta营收强劲，但科技股仍承压。[Reuters市场报道](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-ai-worries-resurface-oil-climbs-ce785cd9d08ff525)、[AP油轮与市场报道](https://apnews.com/article/33767691a4a0730b96d6f0c5100ea9b2)
- 当前策略及主要理由：提交限价减仓方案，主案卖出约一半 TQQQ；若主案未触发，较低限价的备选可退出全部持仓。
- 主要风险：broker最新 TQQQ 估值为前一日 16:00 的 $72.71，标记为 stale；若实际价格低于所有卖出限价，方案可能无法成交。

### 资金与持仓检查

- `cash.available`：$31.15。
- 主方案买入资金需求：$0.00。
- Backup 1 买入资金需求：$0.00。
- Backup 2 买入资金需求：$0.00。
- 预计冻结现金：$0.00。
- 卖出数量检查：主方案卖出 700 股；Backup 1、Backup 2 各卖出 1,393 股。每个候选分别不超过提交前 TQQQ `available_quantity` 1,393 股。broker状态显示冻结股份 1,393 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000003`
  - 有效时间：2026-10-22 08:36 至 12:00（美东时间）
  - broker 整体结果：`ok: true`，状态 `pending`；提交后状态复查确认主方案和两个 backup 均为 `accepted`，尚无成交。
  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：700
      - 限价：$69.00
      - 订单 ID：`ord_000006`
  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：1,393
      - 限价：$64.00
      - 订单 ID：`ord_000007`
  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：TQQQ
      - 数量：1,393
      - 限价：$58.00
      - 订单 ID：`ord_000008`

### 后续计划

- 下轮重点检查：方案成交候选、实际卖出数量、剩余持仓及现金。
- 改变当前判断的条件：若市场迅速反弹且方案未成交，重新评估是否继续持有 TQQQ。