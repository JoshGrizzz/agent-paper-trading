## 2026-10-30T08:35:26.150162-04:00

### 本轮判断

- 市场与关键信息：纳指期货下跌约2.3%，亚马逊盘前跌约7.2%，QQQ外部盘前报价约699.35美元，已跌破705美元风控线。[AP](https://apnews.com/article/16c266731fdf64178f38070af2b42497) [Reuters](https://www.marketscreener.com/news/nasdaq-futures-tumble-as-amazon-intel-results-deepen-ai-spending-woes-ce785fdbd880f125) [QQQ报价](https://www.investing.com/etfs/powershares-qqqq-scoreboard)
- 当前策略及主要理由：分级降低科技敞口；反弹越强，保留的观察仓越多，若弱势延续则彻底退出。
- 主要风险：盘前价格可能快速反弹；反之，若QQQ迅速跌破695美元且无反抽，卖单可能不成交。broker当前估值仍采用昨日16:00的陈旧价格。

### 资金与持仓检查

- `cash.available`：30,950.3550美元
- 主方案买入资金需求：0.00美元
- Backup 1买入资金需求：0.00美元
- Backup 2买入资金需求：0.00美元
- 预计冻结现金：max(0.00, 0.00, 0.00)＝0.00美元；broker实际冻结现金0
- 卖出数量检查：主方案卖出QQQ 60股，Backup 1卖出70股，Backup 2卖出90股，分别不超过提交前`available_quantity`90股；broker按候选最大值冻结90股

### 本轮操作

- 提交交易方案：
  - 方案 ID：`plan_000017`
  - 有效时间：2026-10-30T08:37:00-04:00至2026-10-30T12:00:00-04:00
  - broker 整体结果：`ok: true`，方案状态`pending`；复查确认三个候选均已接受、尚无成交

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：60
      - 限价：705.00美元
      - 订单 ID：`ord_000045`

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：70
      - 限价：701.00美元
      - 订单 ID：`ord_000046`

  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：90
      - 限价：695.00美元
      - 订单 ID：`ord_000047`

### 后续计划

- 下轮重点检查：实际选中候选、成交价格、剩余QQQ数量，以及科技抛售是否扩散至市场其他板块。
- 改变当前判断的条件：若QQQ反弹至705美元以上则保留30股观察仓；若无法触及701美元但仍守住695美元，按Backup 2退出；若方案零成交，午间根据最新价格重新设置风险退出方案。