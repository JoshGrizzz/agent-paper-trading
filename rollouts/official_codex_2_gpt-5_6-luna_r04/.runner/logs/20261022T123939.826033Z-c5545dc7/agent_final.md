## 2026-10-22T08:39:39.766250-04:00

### 本轮判断

- 市场与关键信息：纳指期货跌超 1%，AI 支出担忧升温，SOXL 盘前约 99 美元。[Reuters/MarketScreener](https://www.marketscreener.com/news/nasdaq-futures-drop-over-1-as-investors-digest-earnings-from-meta-and-tesla-ce785cd9d08ff525)
- 当前策略及主要理由：今日限制已重置，优先退出高波动 SOXL，等待更清晰的市场方向。
- 主要风险：卖出限价可能无法成交；半导体板块也可能快速反弹。

### 资金与持仓检查

- `cash.available`：28.0000
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：三组均卖出 SOXL 980 股；提交前 `available_quantity` 为 980，均未超额

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000003
  - 有效时间：2026-10-22T08:41:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：`ok=true`，pending，fills=[]

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：980
      - 限价：100.00
      - 订单 ID：ord_000007

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：980
      - 限价：99.00
      - 订单 ID：ord_000008

  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SOXL
      - 数量：980
      - 限价：98.00
      - 订单 ID：ord_000009

### 后续计划

- 下轮重点检查：方案成交价格、剩余现金及 SOXL 是否清仓。
- 改变当前判断的条件：方案未成交而半导体板块反弹，或 broker 返回新的成交/拒绝状态。