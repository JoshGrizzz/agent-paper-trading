## 2026-10-29T08:36:41.135253-04:00

### 本轮判断

- 市场与关键信息：Nasdaq 100 期指约下跌 1.17%，Alphabet 盘前约跌 10%，Microsoft 约涨 2.8%；科技股分化但指数风险偏下行。[AP](https://apnews.com/article/1b5c71d31b4ce1e46b0db47b33141f6b)、[Investing.com](https://za.investing.com/news/stock-market-news/premarket-movers-microsoft-rises-alphabet-drags-software-stocks-lower-4535089)
- 当前策略及主要理由：用 SQQQ 捕捉指数下行，分档限价降低追高风险。
- 主要风险：Microsoft 强势、Amazon及宏观数据可能带来科技股反弹，SQQQ 杠杆会放大损失。

### 资金与持仓检查

- 提交前 `cash.available`：102,718.3039
- 主方案买入资金需求：2,739 × 37.50 = 102,712.50
- Backup 1 买入资金需求：2,776 × 37.00 = 102,712.00
- Backup 2 买入资金需求：2,814 × 36.50 = 102,711.00
- 预计冻结现金：102,712.50
- 卖出数量检查：无卖单、无持仓；各候选均满足检查。提交后 `cash.available` 为 5.8039，`reserved` 为 102,712.50。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000008`
  - 有效时间：2026-10-29 08:38–12:00 美东
  - broker 整体结果：`ok: true`，方案 pending，当前无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：SQQQ
      - 数量：2,739
      - 限价：37.50
      - 订单 ID：`ord_000022`

  - Backup 1：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：SQQQ
      - 数量：2,776
      - 限价：37.00
      - 订单 ID：`ord_000023`

  - Backup 2：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：SQQQ
      - 数量：2,814
      - 限价：36.50
      - 订单 ID：`ord_000024`

### 后续计划

- 下轮重点检查：方案选择、SQQQ 实际成交价、账户净值及 Nasdaq 是否延续弱势。
- 改变当前判断的条件：指数快速反弹、SQQQ 未成交，或宏观数据显著改善风险偏好。