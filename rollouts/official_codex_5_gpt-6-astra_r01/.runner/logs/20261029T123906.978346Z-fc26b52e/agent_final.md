## 2026-10-29T08:39:06.946961-04:00

### 本轮判断

- 市场与关键信息：Lilly季度收入增长39%，全年收入指引从850–870亿美元提高至910–920亿美元。剔除新增收购研发费用的影响，全年EPS指引中值改善4.07美元；包含该费用后的EPS指引实际降至35–36美元。[公司财报](https://investor.lilly.com/news-releases/news-release-details/lilly-reports-third-quarter-2026-financial-results-raises-full)
- 当前策略及主要理由：限价建立小规模LLY仓位，参与业绩上修并分散科技股风险。08:24盘前参考价为1,355美元，两档限价均低于该报价；保留CDNS和VRT，暂不续挂MSFT。[行情](https://stockanalysis.com/stocks/lly/)
- 主要风险：LLY估值较高、实际售价下降15%，季度收入含约9亿美元特殊收益；10:00电话会可能引发波动，今日买入后不能卖出。[财报与电话会安排](https://www.prnewswire.com/news-releases/lilly-reports-third-quarter-2026-financial-results-raises-full-year-guidance-and-highlights-regulatory-progress-across-the-portfolio-302922907.html)

### 资金与持仓检查

- 提交前 `cash.available`：68,158.00美元。
- 主方案买入资金需求：Σ＝12×1,330.00＝15,960.00美元。
- Backup 1买入资金需求：Σ＝8×1,350.00＝10,800.00美元。
- Backup 2买入资金需求：0.00美元，未提供。
- 两个候选均独立可负担；预计冻结现金为max(15,960.00，10,800.00)＝15,960.00美元，不使用预计卖出收入。
- 卖出数量检查：CDNS `available_quantity`＝60、VRT＝40；各候选均无卖单。

### 本轮操作

- 提交交易方案：`plan_000010`。
- 有效时间：[2026-10-29T08:41:00-04:00，2026-10-29T12:00:00-04:00)。
- broker整体结果：`ok: true`，方案为 `pending`。
- 主方案：`accepted`；买入LLY 12股，限价1,330.00美元，订单 `ord_000019`。
- Backup 1：`accepted`；买入LLY 8股，限价1,350.00美元，订单 `ord_000020`。仅主方案全窗口零成交时检查。
- Backup 2：未提供。
- 提交后独立复查确认两个候选均被接受；实际冻结15,960.00美元，可用现金52,198.00美元，尚无确认成交。
- 昨晚MSFT方案已结束，未形成持仓。当前仍持有CDNS 60股、VRT 40股；账面净值98,420.80美元使用昨日价格，标记为 `stale`，不是当前盘前净值。

### 后续计划

- 午间核实LLY实际成交、电话会内容，以及GDP、PCE数据和市场反应；本轮未取得可核验的最新经济数据结果。
- 若LLY收入上修主要依赖一次性因素，或定价压力超出预期，停止加仓；若成交，遵守当日禁卖限制。
- 检查CDNS和VRT能否保持财报后的涨幅；持续转弱或盈利依据恶化时评估减仓。