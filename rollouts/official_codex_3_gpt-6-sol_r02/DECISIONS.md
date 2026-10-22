# 决策历史

本文件只包含当前轨迹的历史决策，由实验 runner 自动追加。

你可以读取本文件以恢复此前的判断和计划，但不要修改、删除或重写已有记录。

账户余额、持仓、待结算方案、候选接受状态及成交记录始终以 `./broker` 返回的结果为准。

## 2026-10-21T08:32:58.816032-04:00

### 本轮判断

- 市场与关键信息：[SpaceX 季报](https://www.sec.gov/Archives/edgar/data/1181412/000162828026066482/spaceexplorationtechnologi.htm)显示收入同比增长 161%，但资本开支达 195.93 亿美元。
- 当前策略及主要理由：限价买入 SPCX 与 SOXL，争取参与业绩后的上涨；若主方案零成交，依次尝试 TQQQ、SPY。
- 主要风险：SPCX 盘前已上涨，可能回落；[SOXL](https://www.direxion.com/product/daily-semiconductor-bull-bear-3x-etfs)和[TQQQ](https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq)均为每日三倍杠杆 ETF，波动较大。

### 资金与持仓检查

- 提交前 `cash.available`：100000.00 美元。
- 主方案买入资金需求：360 × 162.00 ＋ 390 × 104.00 ＝ 98880.00 美元。
- Backup 1 买入资金需求：1360 × 73.00 ＝ 99280.00 美元。
- Backup 2 买入资金需求：128 × 775.00 ＝ 99200.00 美元。
- 预计冻结现金：99280.00 美元；broker 实际冻结 99280.00 美元，提交后 `cash.available` 为 720.00 美元。
- 卖出数量检查：三个候选方案均无卖单；提交前无持仓。

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000001
  - 有效时间：2026-10-21T08:35:00-04:00 至 2026-10-21T12:00:00-04:00
  - broker 整体结果：`ok: true`；再次查询状态确认方案待结算，尚无成交。
  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入；标的：SPCX；数量：360；限价：162.00；订单 ID：ord_000001
      - 操作：买入；标的：SOXL；数量：390；限价：104.00；订单 ID：ord_000002
  - Backup 1：
    - broker 状态：accepted
    - 订单：
      - 操作：买入；标的：TQQQ；数量：1360；限价：73.00；订单 ID：ord_000003
  - Backup 2：
    - broker 状态：accepted
    - 订单：
      - 操作：买入；标的：SPY；数量：128；限价：775.00；订单 ID：ord_000004

### 后续计划

- 下轮重点检查：12:00 结算后的实际成交、持仓估值，以及未投入现金。
- 改变当前判断的条件：SPCX 业绩反应转弱、半导体板块回落，或市场方向明显逆转。

## 2026-10-21T12:02:27.348159-04:00

### 本轮判断

- 市场与关键信息：broker 确认持有 SPCX 360 股、SOXL 390 股；账户净值 101362.3510 美元。[META](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-to-Announce-Third-Quarter-2026-Results/default.aspx)和[TSLA](https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments)均计划今晚盘后发布财报。
- 当前策略及主要理由：现有持仓约占净值 98%；保留剩余现金，本轮不加仓。
- 主要风险：SOXL 为每日三倍杠杆 ETF；今晚的财报可能引发科技股波动。今天买入的 SPCX、SOXL 当日不得卖出。

### 资金与持仓检查

- `cash.available`：2084.9500 美元。
- 主方案买入资金需求：0.00 美元。
- Backup 1 买入资金需求：0.00 美元。
- Backup 2 买入资金需求：0.00 美元。
- 预计冻结现金：0.00 美元；broker 确认 `cash.reserved` 为 0。
- 卖出数量检查：本轮无卖单。broker 显示 SPCX、SOXL 的 `available_quantity` 分别为 360、390 股。

### 本轮操作

- 不操作：
  - 原因：现有持仓已使用大部分账户资金；本轮未提交主方案或 backup。复查 broker 状态确认无待结算方案、无本次查询新成交。

### 后续计划

- 下轮重点检查：持仓价格及今晚 META、TSLA 财报后的市场反应。
- 改变当前判断的条件：SPCX 业绩后的涨势逆转，或半导体板块明显转弱。

## 2026-10-21T15:37:06.611762-04:00

### 本轮判断

- 市场与关键信息：[美股盘中上涨](https://apnews.com/article/4fa93685cd49e51e7ff0d840fdd38b0d)，但 broker 对 SPCX、SOXL 的估值仍使用 11:59 行情，状态为 `stale`，不能视作当前净值。
- 当前策略及主要理由：保留现有 SPCX 360 股、SOXL 390 股和剩余现金；本轮不加仓。
- 主要风险：[META](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-to-Announce-Third-Quarter-2026-Results/default.aspx)与[TSLA](https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments)今晚盘后发布财报，科技股可能大幅波动；今天买入的现有持仓当日不得卖出。

### 资金与持仓检查

- `cash.available`：2084.9500 美元。
- 主方案买入资金需求：0.00 美元。
- Backup 1 买入资金需求：0.00 美元。
- Backup 2 买入资金需求：0.00 美元。
- 预计冻结现金：0.00 美元；broker 显示实际冻结现金为 0。
- 卖出数量检查：本轮无卖单；SPCX、SOXL 的 `available_quantity` 分别为 360、390 股。

### 本轮操作

- 不操作：
  - 原因：本轮未提交主方案或 backup，均无本轮接受状态。再次查询 broker 确认无待结算方案、无新成交；持仓估值仍为 `stale`。

### 后续计划

- 下轮重点检查：更新后的 broker 估值及盘后财报对 SPCX、SOXL 的影响。
- 改变当前判断的条件：取得新鲜行情后，现有持仓的走势或科技股前景明显转弱。

## 2026-10-21T19:05:56.831939-04:00

### 本轮判断

- 市场与关键信息：[Tesla 财报](https://ir.tesla.com/_flysystem/s3/sec/000162828026066738/tsla-20261021-gen.pdf)显示季度净利润同比下降；[Meta 财报](https://www.marketscreener.com/news/meta-reports-third-quarter-2026-results-ce785cd9dd8cf620)显示收入同比增长。broker 对 SPCX、SOXL 仍使用 11:59 行情，账户估值为 `stale`。
- 当前策略及主要理由：保留 SPCX 360 股、SOXL 390 股及剩余现金，等待新鲜行情再调整。
- 主要风险：盘后业绩可能引发隔夜波动；今天买入的 SPCX、SOXL 当日不得卖出。

### 资金与持仓检查

- `cash.available`：2084.9500 美元。
- 主方案买入资金需求：0.00 美元。
- Backup 1 买入资金需求：0.00 美元。
- Backup 2 买入资金需求：0.00 美元。
- 预计冻结现金：0.00 美元；broker 确认实际冻结现金为 0。
- 卖出数量检查：本轮无卖单；SPCX、SOXL 的 `available_quantity` 分别为 360、390 股。

### 本轮操作

- 不操作：
  - 原因：本轮未提交主方案或 backup，因此均无本轮接受状态。再次查询 broker 确认无待结算方案、无新成交；持仓估值仍为 `stale`。

### 后续计划

- 下轮重点检查：broker 更新后的持仓估值，以及财报后 SPCX、SOXL 的走势。
- 改变当前判断的条件：取得新鲜行情后，科技股或现有持仓明显转弱。
