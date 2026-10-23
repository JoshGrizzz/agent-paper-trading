## 2026-10-22T08:33:56.149655-04:00

### 本轮判断

- 市场与关键信息：[凌晨纳指期货跌约 1.6%，Lam Research 财报后走弱](https://www.cannontrading.com/tools/daily-updates/uploads/briefing-oct22-2026-readers-web-v1.html)；[SOXL 盘前报价约 $91.93](https://www.google.com/finance/quote/SOXL:NYSEARCA)。broker 持仓估值仍停在昨日 11:59，状态为 `stale`。
- 当前策略及主要理由：为降低半导体杠杆敞口，提交三个互斥的 SOXL 全额卖出限价候选；暂持 QQQ 和 SMCI。
- 主要风险：盘前价格波动大，限价可能无法成交；卖出后也可能错过反弹。

### 资金与持仓检查

- `cash.available`：提交前及提交后均为 $1,004.3550。
- 主方案买入资金需求：$0.00。
- Backup 1 买入资金需求：$0.00。
- Backup 2 买入资金需求：$0.00。
- 预计冻结现金：$0.00；broker 确认冻结现金 $0。
- 卖出数量检查：每个候选均卖出 SOXL 500 股，分别不超过提交前的 `available_quantity` 500 股；候选互斥，broker 确认冻结 SOXL 500 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000002`
  - 有效时间：2026-10-22T08:36:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：`ok: true`；提交后再次查询，方案仍待结算，尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：500
      - 限价：$92.00
      - 订单 ID：`ord_000006`

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：无
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：500
      - 限价：$89.00
      - 订单 ID：`ord_000007`

  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：无
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：500
      - 限价：$85.00
      - 订单 ID：`ord_000008`

### 后续计划

- 下轮重点检查：12:00 后以 broker 状态确认实际选中候选、成交价格及可用现金。
- 改变当前判断的条件：半导体与纳指走势企稳，或 SOXL 三个限价均未触发。