## 2026-10-29T19:12:46.339669-04:00

### 本轮判断

- 市场与关键信息：亚马逊过去十二个月自由现金流为负424亿美元；英特尔第四季度指引低于预期，科技股盘后承压。[亚马逊公告](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Third-Quarter-Results/default.aspx)；[Reuters报道](https://live.euronext.com/en/financial-news/intel-shares-drop-18-israel-factory-blast-pc-weakness)。
- 当前策略及主要理由：限价减持一半QQQ。其18:53参考价702.70美元、盘后下跌1.77%，此前反弹转弱；保留CDNS、LLY及XLE。[QQQ行情](https://stockanalysis.com/etf/qqq/)。
- 主要风险：减仓可能错过反弹；限价及盘后分钟成交量条件可能导致未成交。broker估值过期，刷新返回`INTERNAL_ERROR`。

### 资金与持仓检查

- 提交前`cash.available`：46,673.10美元。
- 主方案买入资金需求：Σ(数量×限价)＝0.00美元，无买单。
- Backup 1买入资金需求：0.00美元，未提供。
- Backup 2买入资金需求：0.00美元，未提供。
- 预计冻结现金：0.00美元；broker确认一致，不使用预计卖出收入。
- 卖出数量检查：QQQ卖出15股≤提交前`available_quantity=30`；CDNS、LLY、XLE分别可用30、8、100股，均不卖出。LLY今日买入，遵守当日禁卖限制。
- broker确认LLY持仓8股、均价1,368美元，与午间Backup 1一致。账户权益96,281.80美元，为收盘附近旧报价估值。

### 本轮操作

- 提交交易方案：
  - 方案ID：`plan_000012`。
  - 有效时间：`[2026-10-29T19:16:00-04:00, 2026-10-29T20:00:00-04:00)`。
  - broker整体结果：`ok=true`，方案`pending`。
  - 主方案：
    - broker状态：`accepted`。
    - 订单：操作：卖出；标的：QQQ；数量：15股；限价：699.00美元；订单ID：`ord_000022`。
  - Backup 1：未提供；拒绝原因及订单ID不适用。
  - Backup 2：未提供；拒绝原因及订单ID不适用。
- 19:15:26再次查询，确认主方案已接受、两个backup均未提供。QQQ总持仓30股、冻结15股、可用15股；现金可用46,673.10美元、冻结0。尚无本方案成交确认。

### 后续计划

- 下轮核对卖单结算、剩余QQQ及盘前报价，检查LLY财报涨幅和CDNS相对强势是否保持。
- 若科技股继续下跌且CDNS同步转弱，评估进一步减仓；若市场企稳并出现新的业绩催化，再部署现金。