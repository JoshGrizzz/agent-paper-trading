## 2026-10-21T08:36:38.761095-04:00

### 本轮判断

- 市场与关键信息：10/20 收盘：S&P 500 7,712.57（+0.28%），道指 +1%，纳指持平，罗素 2000 +1.65%。10/21 盘前股指期货偏强，纳指约 +0.4%~+0.7%，S&P 约 +0.2%。SpaceX（SPCX）财报超预期，盘前约 +9%，AI/半导体跟涨，SMCI 上调指引，盘前约 +16%。NFLX 盘前约 -6%。Wells Fargo 情绪指标给出逆向"买入"信号。风险方面：Brent 超过 110 美元（伊朗在霍尔木兹海峡拦截油轮），10 年期美债收益率约 5.1%。今天盘后 TSLA、META、IBM 发布财报，美联储 10/28 公布议息结果。盘前报价：SPY 770.90，QQQ 721.90，SMH 555.83，XLE 67.96。SMH 52 周高点为 671.83，目前较高点回落约 19%。来源：[Fortune](https://fortune.com/2026/10/21/tech-futures-rise-premarket-trading-spacex-stock-rockets-overnight-wells-fargos-buy-signal-triggered/)、[Stocktwits](https://stocktwits.com/news-articles/markets/equity/nasdaq-futures-rise-premarket-spacex-ai-boom-lifts-chip-stocks-smci-tsla-meta-ibm-crwv-nflx-be-in-focus/cZxtvuZRBHU)、[STL.News](https://www.stl.news/stock-market-today-dow-surges-nearly-530-points/)、[Yahoo SPY](https://finance.yahoo.com/quote/SPY/)。
- 当前策略及主要理由：首轮建仓，股票仓位约 92%。以 SPY 和 QQQ 宽基为核心；SMH 回调幅度大，且有 AI 需求催化，作为进攻部分；XLE 用来对冲油价和中东风险。限价贴近盘前价格。主方案零成交时，Backup 1 用略高的限价追价建仓。
- 主要风险：油价或地缘局势进一步恶化，美债收益率继续上升；盘后 TSLA/META 财报不及预期，拖累科技股；AI 泡沫论升温；XLE 已接近 52 周高点。

### 资金与持仓检查

- `cash.available`：100000.00
- 主方案买入资金需求：55×770.50 + 40×721.00 + 20×553.00 + 150×68.00 = 42377.50 + 28840.00 + 11060.00 + 10200.00 = 92477.50
- Backup 1 买入资金需求：55×775.00 + 40×726.00 + 20×558.00 + 150×68.60 = 42625.00 + 29040.00 + 11160.00 + 10290.00 = 93115.00
- Backup 2 买入资金需求：未提供（0.00）
- 预计冻结现金：93115.00（broker 返回 reservation.cash = 93115.00，提交后 cash.available = 6885.00）
- 卖出数量检查：无卖单，账户无持仓，不涉及

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000001
  - 有效时间：2026-10-21T08:39:00-04:00 至 2026-10-21T12:00:00-04:00
  - broker 整体结果：ok = true，status = pending

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：SPY
      - 数量：55
      - 限价：770.50
      - 订单 ID：ord_000001
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：40
      - 限价：721.00
      - 订单 ID：ord_000002
    - 订单：
      - 操作：买入
      - 标的：SMH
      - 数量：20
      - 限价：553.00
      - 订单 ID：ord_000003
    - 订单：
      - 操作：买入
      - 标的：XLE
      - 数量：150
      - 限价：68.00
      - 订单 ID：ord_000004

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：买入
      - 标的：SPY
      - 数量：55
      - 限价：775.00
      - 订单 ID：ord_000005
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：40
      - 限价：726.00
      - 订单 ID：ord_000006
    - 订单：
      - 操作：买入
      - 标的：SMH
      - 数量：20
      - 限价：558.00
      - 订单 ID：ord_000007
    - 订单：
      - 操作：买入
      - 标的：XLE
      - 数量：150
      - 限价：68.60
      - 订单 ID：ord_000008

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：plan_000001 选中了哪个候选，各订单是否成交及成交价；主方案选中后可能只有部分订单成交，需要用剩余现金补齐。关注 TSLA/META/IBM 盘后财报、油价和霍尔木兹海峡局势、10 年期美债收益率。
- 改变当前判断的条件：Brent 继续大涨，或者地缘冲突升级、10 年期收益率明显突破 5.2%，就降低 QQQ/SMH 仓位、增加 XLE 或现金。科技股财报大幅不及预期，就减持 SMH/QQQ。若市场在逆向买入信号后企稳上行，就保持核心仓位，再考虑加仓半导体。