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