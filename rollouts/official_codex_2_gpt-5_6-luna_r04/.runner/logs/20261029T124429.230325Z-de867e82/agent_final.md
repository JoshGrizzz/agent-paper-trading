## 2026-10-29T08:44:29.196651-04:00

### 本轮判断

- 纳指期货约跌 1.1%，QQQ 盘前约跌 1%；Alphabet 弱势压过 Microsoft 利好。[Reuters市场报道](https://www.investing.com/news/economy-news/nasdaq-futures-slide-as-mixed-big-tech-results-test-ai-trade-4981842) [QQQ盘前报价](https://stockmarketwatch.com/stock/QQQ/premarket)
- 分层卖出全部 QQQ，优先控制财报后的科技板块下行风险。
- 主要风险：盘前成交量门槛或价格条件导致卖出不成交，随后市场反弹。

### 资金与持仓检查

- `cash.available`：343.9400
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：提交前 QQQ `available_quantity=123`；主方案、Backup 1、Backup 2 均卖出 123 股，未超额。复核后 QQQ `available_quantity=0`、冻结 123 股。

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000014`
  - 有效时间：2026-10-29T08:45:00-04:00 至 2026-10-29T12:00:00-04:00
  - broker 整体结果：`ok=true`，pending，fills=[]

  - 主方案：accepted
    - 卖出 QQQ 123 股，限价 717.00，订单 ID `ord_000039`

  - Backup 1：accepted
    - 卖出 QQQ 123 股，限价 715.50，订单 ID `ord_000040`

  - Backup 2：accepted
    - 卖出 QQQ 123 股，限价 714.00，订单 ID `ord_000041`

### 后续计划

- 下轮检查方案是否成交、实际卖出价格及剩余现金。
- 若全部未成交且市场企稳，将重新评估 QQQ 的常规时段卖出限价。