## 2026-10-22T08:37:46.929120-04:00

### 本轮判断

- 市场与关键信息：[纳指期货今早下跌逾 1%](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-ai-worries-resurface-oil-climbs-ce785cd9d08ff525)；盘前报价显示 [SOXL 约跌 10.7%](https://stockmarketwatch.com/stock/SOXL/premarket)、[SMCI 约跌 3.7%](https://stockmarketwatch.com/stock/SMCI/premarket)。broker 持仓估值仍停留在昨日 11:59。
- 当前策略及主要理由：为高波动的 SOXL 设置分层限价卖出方案，计划减持 400 股；保留其余 150 股及 SMCI 持仓。
- 主要风险：盘前报价和实际成交价可能不同；方案到期前若三个卖出限价均未触及，则不会减仓。

### 资金与持仓检查

- `cash.available`：$7,009.6500。
- 主方案买入资金需求：$0.00。
- Backup 1 买入资金需求：$0.00。
- Backup 2 买入资金需求：$0.00。
- 预计冻结现金：$0.00；broker 确认冻结 $0.00。
- 卖出数量检查：每个候选均只卖出 SOXL 400 股，分别不超过提交前 `available_quantity` 550 股；broker 实际冻结 SOXL 400 股，三个候选互斥。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000002`
  - 有效时间：2026-10-22T08:40:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：`ok: true`，待结算；提交后再次查询，确认主方案及两个 backup 均获接受，尚无成交。
  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出；标的：SOXL；数量：400；限价：$102.75；订单 ID：`ord_000005`
  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出；标的：SOXL；数量：400；限价：$96.00；订单 ID：`ord_000006`
  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出；标的：SOXL；数量：400；限价：$80.00；订单 ID：`ord_000007`

### 后续计划

- 下轮重点检查：12:00 后以 broker 确认选中的候选、实际成交价、持仓及更新后的净值。
- 改变当前判断的条件：半导体板块持续反弹或 SMCI 的公司信息出现变化。