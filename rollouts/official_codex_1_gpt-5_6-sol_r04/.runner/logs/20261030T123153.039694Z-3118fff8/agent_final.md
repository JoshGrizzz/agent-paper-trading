## 2026-10-30T08:31:53.028328-04:00

### 本轮判断
TMF 盘前约 29.72，高于 29.22 的持仓成本；科技股期货走弱且长期美债价格上涨，有利于锁定隔夜收益。[TMF 报价](https://robinhood.com/us/en/stocks/TMF/) [市场概况](https://strongbuyanalytics.com/stock-market-outlook/2026-10-30) 考虑 TMF 的三倍日杠杆及 09:45 Chicago PMI 的反转风险，选择分层退出全部持仓。

### 资金与持仓检查
操作前 cash.available 为 303.4401 美元，TMF available_quantity 为 3,593 股。主方案及两个 backup 的买单金额均为 0，互斥候选最大预计冻结现金为 0；各候选均卖出 3,593 股，不超过可卖数量，且未使用预计卖出收入支付买单。

### 本轮操作
提交交易方案 `plan_000014`：

- 主方案：限价 30.00 美元卖出 TMF 3,593 股，accepted。
- Backup 1：限价 29.70 美元卖出 TMF 3,593 股，accepted。
- Backup 2：限价 0.01 美元卖出 TMF 3,593 股，accepted。

方案状态为 pending，有效期 08:34–12:00。复查显示现金冻结 0，TMF 3,593 股全部冻结，available_quantity 为 0，三个候选均已被 broker 接受。

### 后续计划
下一轮首先核对实际成交候选、成交价格和现金余额；若完成退出，再根据最新利率与市场方向重新配置资金。