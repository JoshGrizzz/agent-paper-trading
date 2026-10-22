## 2026-10-21T19:03:51.904666-04:00

### 本轮判断

- 市场与关键信息：[Lam Research](https://investor.lamresearch.com/2026-10-21-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-September-27%2C-2026)与[Texas Instruments](https://investor.ti.com/static-files/92651fc5-a8bf-4327-b864-55e178f45abd)公布较强季度结果；broker 的 SOXL 估值仍停在 11:59，已标为过期。
- 当前策略及主要理由：持有 SOXL 800 股，并用余款设置收盘后回落买入限价，优先增持 SOXL。
- 主要风险：盘后流动性较低，杠杆 ETF 波动大；本轮订单尚未确认成交。

### 资金与持仓检查

- 提交前 `cash.available`：$18,400.00
- 主方案买入资金需求：170 × $103.00 = $17,510.00
- Backup 1 买入资金需求：240 × $72.75 = $17,460.00
- Backup 2 买入资金需求：115 × $152.00 = $17,480.00
- 预计冻结现金：$17,510.00；broker 确认冻结 $17,510.00，剩余可用现金 $890.00。
- 卖出数量检查：三个候选均无卖单；提交前 SOXL `available_quantity` 为 800 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000002`
  - 有效时间：2026-10-21T19:05:00-04:00 至 2026-10-21T20:00:00-04:00
  - broker 整体结果：`ok: true`；复查时方案为 `pending`，无新增成交。
  - 主方案：`accepted`；买入 SOXL 170 股，限价 $103.00，订单 `ord_000004`。
  - Backup 1：`accepted`；买入 TQQQ 240 股，限价 $72.75，订单 `ord_000005`。
  - Backup 2：`accepted`；买入 UPRO 115 股，限价 $152.00，订单 `ord_000006`。

### 后续计划

- 下轮重点检查：broker 对本方案的选择和实际成交、释放的冻结现金，以及 SOXL 的新鲜估值。
- 改变当前判断的条件：半导体业绩指引或市场反应转弱。