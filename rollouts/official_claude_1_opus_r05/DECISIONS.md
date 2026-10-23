# 决策历史

本文件只包含当前轨迹的历史决策，由实验 runner 自动追加。

你可以读取本文件以恢复此前的判断和计划，但不要修改、删除或重写已有记录。

账户余额、持仓、待结算方案、候选接受状态及成交记录始终以 `./broker` 返回的结果为准。

## 2026-10-21T08:38:36.332173-04:00

### 本轮判断

- 市场与关键信息：10/20 收盘 S&P 500 涨 0.28% 至 7,712.57；道指涨 1.02%；纳指基本持平；罗素 2000 涨 1.65%。今天盘前期货走高：标普 +0.3%，纳指 100 +0.7%。SMCI 上调指引后盘后涨约 12.7%，带动半导体盘前反弹：SMH 盘前约 555.9（+1.7%），NVDA 约 220.2（+1.7%）。SPY 盘前约 771.2，QQQ 盘前约 722.4。NFLX 盘后跌约 5.7%。今天收盘后 META、TSLA、IBM、LRCX、TXN 发布财报。宏观方面，10 年期美债收益率约 5.1%，Brent 原油约 $109–110（霍尔木兹海峡油轮遭袭），FOMC 会议在 10/27–28。来源：[Yahoo 盘前直播](https://finance.yahoo.com/markets/live/stock-market-today-wednesday-october-21-dow-sp-500-nasdaq-100000105.html)、[Closing Look 10/20](https://cappnotes.substack.com/p/closing-look-tuesday-october-20-2026)、[Bloomberg](https://www.bloomberg.com/news/articles/2026-10-20/stock-market-today-dow-s-p-live-updates)、Yahoo 报价页（SPY/QQQ/SMH/NVDA）。
- 当前策略及主要理由：这是首轮建仓，投入约 87.5% 资金，配置宽基加科技/半导体：QQQ 约 40%、SPY 约 31%、SMH 约 17%。上周的回调已经开始修复，AI 财报情绪偏强，所以顺势持有 beta 敞口。剩余约 12.5% 现金，用于应对财报或 FOMC 的波动。限价略高于盘前价，目的是确保成交。主方案若完全未成交，说明市场跳涨并持续高于限价，此时 backup 用更高限价追入。
- 主要风险：META/TSLA 财报不及预期，拖累科技股；10 年期收益率超过 5% 加上油价超过 $100 带来通胀和估值压力；FOMC 偏鹰；AI 资本开支和债务方面的担忧可能再次出现。

### 资金与持仓检查

- `cash.available`：100000.00（提交前）
- 主方案买入资金需求：55×724.50 + 40×773.00 + 30×558.00 = 39847.50 + 30920.00 + 16740.00 = 87507.50
- Backup 1 买入资金需求：50×778.00 + 50×731.00 = 38900.00 + 36550.00 = 75450.00
- Backup 2 买入资金需求：100×785.00 = 78500.00
- 预计冻结现金：87507.50（三个候选取最大值；broker 返回的冻结现金同为 87507.50，提交后 available 为 12492.50）
- 卖出数量检查：没有卖单，当前无持仓，不适用

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000001
  - 有效时间：2026-10-21T08:40:00-04:00 至 2026-10-21T12:00:00-04:00
  - broker 整体结果：ok=true，状态 pending。提交后 status 确认方案在 open_plans 中，冻结现金 87507.50。尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：55
      - 限价：724.50
      - 订单 ID：ord_000001
    - 订单：
      - 操作：买入
      - 标的：SPY
      - 数量：40
      - 限价：773.00
      - 订单 ID：ord_000002
    - 订单：
      - 操作：买入
      - 标的：SMH
      - 数量：30
      - 限价：558.00
      - 订单 ID：ord_000003

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：买入
      - 标的：SPY
      - 数量：50
      - 限价：778.00
      - 订单 ID：ord_000004
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：50
      - 限价：731.00
      - 订单 ID：ord_000005

  - Backup 2：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：买入
      - 标的：SPY
      - 数量：100
      - 限价：785.00
      - 订单 ID：ord_000006

### 后续计划

- 下轮重点检查：12:00 结算后，确认主方案的实际成交价和数量，以及哪个候选被选中。关注 10:30 EIA 原油库存、盘中油价和美债收益率走势。15:30 那一轮判断是否在 META/TSLA 盘后财报前降低科技敞口，或保持仓位。可考虑用剩余现金做小仓位配置，例如能源或黄金对冲。
- 改变当前判断的条件：标普盘中由涨转跌并跌超 1%；10 年期收益率大幅升破 5.2%；油价继续飙升（Brent 超过 $115）；META/TSLA 财报明显不及预期，盘后大跌。出现上述情况时考虑减仓 QQQ/SMH，或增加防御类和现金比例。

## 2026-10-21T12:04:44.410620-04:00

### 本轮判断

- 市场与关键信息：plan_000001 的主方案已全部成交。成交均价：QQQ 55 股 722.22、SPY 40 股 771.17、SMH 30 股 556.55。backups 已失效。截至 11:59，QQQ 726.22、SPY 772.67、SMH 557.48，账户净值约 100,307.90（+0.31%）。今天开盘后三大指数小幅走高，科技和 AI 领涨（SMCI、SpaceX）；NFLX 拖累通信板块。10 年期美债收益率约 5.08%，Brent 约 $110，黄金约 $4,150。XLE 现价约 68.03，GLD 约 378.63。收盘后 META、TSLA、IBM、LRCX、TXN 发布财报。来源：[Investrade Mid-Morning Look](https://investrade.com/mid-morning-look-october-21-2026/)、[Sunday Guardian 开盘报道](https://sundayguardianlive.com/business/us-stock-market-today-live-dow-jones-rises-030-sp-500-gains-031-and-nasdaq-jumps-067-at-open-as-spacex-and-super-micro-boost-ai-stocks-check-latest-wall-street-updates-309660/)、[moomoo 市场更新](https://www.moomoo.com/community/feed/wednesday-market-update-october-21-2026-117477748834310)、Yahoo 报价页（XLE/GLD）。
- 当前策略及主要理由：继续持有核心 beta 仓位（QQQ/SPY/SMH）。用剩余约 1.27 万现金中的约 1 万买入 XLE（约 10%）。原油处在 $100 以上，霍尔木兹海峡风险仍在；能源仓位可以对冲油价冲击导致科技估值承压的情景，也让组合更分散。
- 主要风险：META/TSLA 财报不及预期，可能导致 QQQ/SMH 盘后下跌，而今天已买入的仓位当日不能卖出；油价若因局势缓和而回落，XLE 会下跌；美债收益率可能再次升破 5.2%。

### 资金与持仓检查

- `cash.available`：12734.6000（提交前）
- 主方案买入资金需求：150×68.20 = 10230.00
- Backup 1 买入资金需求：145×68.80 = 9976.00
- Backup 2 买入资金需求：未提供，0.00
- 预计冻结现金：10230.00（取最大值）。broker 返回冻结现金 10230.00，提交后 available 为 2504.6000
- 卖出数量检查：没有卖单，不适用。当前 available_quantity 为 QQQ 55、SPY 40、SMH 30

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000002
  - 有效时间：2026-10-21T12:06:00-04:00 至 2026-10-21T15:30:00-04:00
  - broker 整体结果：ok=true，状态 pending。提交后 status 确认方案在 open_plans 中，冻结现金 10230.00。尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：XLE
      - 数量：150
      - 限价：68.20
      - 订单 ID：ord_000007

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：买入
      - 标的：XLE
      - 数量：145
      - 限价：68.80
      - 订单 ID：ord_000008

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：15:30 结算后，确认 XLE 是否成交及成交价。观察尾盘大盘走势。META/TSLA 收盘后发布财报，今天买入的 QQQ/SPY/SMH 当日不能卖出，19:00 那一轮结合盘后反应评估明天是否调整科技敞口。
- 改变当前判断的条件：META/TSLA 财报不及预期，盘后纳指期货下跌超过 1%，则考虑明天减仓 QQQ/SMH；油价急跌或霍尔木兹局势缓和，则重新评估 XLE；财报明显超预期且半导体走强，则考虑把仓位向 SMH/QQQ 集中。

## 2026-10-21T15:32:38.429859-04:00

### 本轮判断

- 市场与关键信息：plan_000002 的主方案已成交：XLE 150 股，均价 68.00，最新 68.225。QQQ 下午 3:32 报 725.94，较昨日收盘涨 1.16%，日内区间 719.72–727.95，科技股全天走强。账户净值约 100,341.65（+0.34%）；QQQ/SPY/SMH 的 broker 估值价格停在 11:59，标记为 stale。今天收盘后 META、TSLA、IBM、LRCX、TXN 发布财报。本轮搜索没有找到 10/21 下午的综合市场报道（结果为 [maremagnum](https://billing.maremagnum.com/blog/stock-market-today-dow-nasdaq-sandp-500-movement-1764807187)、[indmoney](https://www.indmoney.com/us-market-today) 等泛化或过期页面），盘中价格以 Yahoo QQQ 报价页为准。
- 当前策略及主要理由：持仓已基本满仓：QQQ 约 40%、SPY 约 31%、SMH 约 17%、XLE 约 10%，现金约 2.5%。全部持仓都是今天买入的，按日内方向限制今天不能卖出。剩余现金只有约 2,534.60，加仓意义不大，留作缓冲。本轮不操作，等待 META/TSLA 盘后财报结果。
- 主要风险：META/TSLA 财报不及预期，可能导致科技股隔夜跳空低开；美债收益率和油价可能再度走高；FOMC 会议（10/27–28）前市场可能转向谨慎。

### 资金与持仓检查

- `cash.available`：2534.6000
- 主方案买入资金需求：0.00（未提交）
- Backup 1 买入资金需求：0.00（未提交）
- Backup 2 买入资金需求：0.00（未提交）
- 预计冻结现金：0.00
- 卖出数量检查：没有卖单。available_quantity 为 QQQ 55、SPY 40、SMH 30、XLE 150，全部为今天买入，今天不能卖出

### 本轮操作

- 不操作：
  - 原因：持仓已接近满仓，全部是今天买入，今天受日内方向限制不能卖出；剩余现金约 2.5k，金额太小，不值得加仓。等 META/TSLA 财报公布后，再在 19:00 或明早调整。

### 后续计划

- 下轮重点检查：19:00 查看 META、TSLA、IBM、LRCX、TXN 的财报内容和盘后反应，以及 QQQ/SMH 的盘后价格。明早 08:30 根据盘前走势决定是否调整科技和半导体敞口（今天的持仓明天起可以卖出）。同时关注油价和 10 年期美债收益率。
- 改变当前判断的条件：META/TSLA 财报明显不及预期、纳指期货跌超 1%，则明天减仓 QQQ/SMH，提高现金或防御类仓位；财报超预期、半导体走强（LRCX/TXN 指引好），则继续持有并考虑向 SMH 集中；油价急跌，则考虑卖出 XLE。

## 2026-10-21T19:03:18.444938-04:00

### 本轮判断

- 市场与关键信息：今天常规时段，QQQ 收 725.20（+1.05%），SMH 收 556.70（+1.89%）。盘后 QQQ 约 721.12（-0.56%），SMH 约 551.50（-0.93%）。盘后个股：META 约 +4%，Q3 营收 $64.6B、EPS $3.83 超预期，Q4 指引 $73–76B 高于共识，并宣布 2 拆 1 和新的无投票权股；IBM 约 +6%；TSLA 小幅波动，EPS $0.48 超预期，营收与预期大致一致，盘后报道方向不一；LRCX 约 -6%，原因是获利了结，KLAC/AMAT 可能跟跌；CSX 约 +5%；LVS 约 -4%。broker 中 QQQ/SPY/SMH 的估值价格仍停在 11:59（stale），账户净值约 100,341.65。来源：[Investing.com 盘后异动](https://www.investing.com/news/stock-market-news/afterhours-movers-meta-ibm-tsla-lrcx-klac-amat-csx-kmi-lvs-432SI-4964053)、[TipRanks](https://www.tipranks.com/news/why-meta-stock-is-rising-after-hours-while-tesla-falls-and-what-wall-street-sees-next)、[Yahoo 财报直播](https://finance.yahoo.com/markets/live/earnings-live-updates-all-eyes-on-musk-and-meta-as-q3-earnings-roll-on-134152191.html)、[CNBC 盘后异动](https://www.cnbc.com/2026/10/21/stocks-making-the-biggest-moves-after-hours-meta-tsla-lrcx-ibm.html)（403 无法读取）、Yahoo 报价页（QQQ/SMH）。
- 当前策略及主要理由：继续持有 QQQ/SPY/SMH/XLE。财报整体偏正面，META、IBM 超预期，盘后的小幅回落主要来自半导体设备股（LRCX）获利了结，不构成明显的利空信号。全部持仓都是今天买入，按日内方向限制今天不能卖出；剩余现金只有约 2.5k，也不值得加仓。所以本轮不操作。
- 主要风险：半导体设备板块的获利了结可能延续，拖累 SMH；美债收益率约 5.1%，原油约 $110，宏观压力仍在；FOMC 会议（10/27–28）临近。

### 资金与持仓检查

- `cash.available`：2534.6000
- 主方案买入资金需求：0.00（未提交）
- Backup 1 买入资金需求：0.00（未提交）
- Backup 2 买入资金需求：0.00（未提交）
- 预计冻结现金：0.00
- 卖出数量检查：没有卖单。available_quantity 为 QQQ 55、SPY 40、SMH 30、XLE 150，全部为今天买入，今天不能卖出

### 本轮操作

- 不操作：
  - 原因：持仓全部是今天买入，今天不能卖出；现金约 2.5k，金额太小，不值得加仓。META/IBM 财报偏正面，盘后指数只是小幅波动，不需要调整。明早 08:30 根据盘前走势再决定。

### 后续计划

- 下轮重点检查：明早 08:30 查看盘前 QQQ/SMH/SPY 和 LRCX/KLAC/AMAT 的走势、10 年期美债收益率、原油价格，以及 10/22 盘前财报。到时持仓已可以卖出，可评估是否把 SMH 部分换成 QQQ，或换成 META 等受益于财报的个股。
- 改变当前判断的条件：盘前纳指期货跌超 1%，或半导体继续大跌（SMH 跌超 2%），则考虑减仓 SMH；原油急跌（Brent 低于 $100），则考虑卖出 XLE；市场普遍上涨、科技股领涨，则继续持有。

## 2026-10-22T08:32:05.664075-04:00

### 本轮判断

- 市场与关键信息：今天盘前明显转弱。纳指 100 期货约 -1.9%，标普期货约 -1.1%，道指期货约 -0.7%。主要原因是市场对 AI 资本开支回报的担忧再起：META 把 2026 年资本开支下限上调到 $135B；TSLA 下调资本开支，盘前约 -5%；LRCX 盘前跌超 7%；INTC、MRVL、AMD 跌超 4%。伊朗局势升级：特朗普表示美国不与德黑兰谈判，沙特遭无人机袭击，Brent 升破 $112，WTI 接近 $100。10 年期美债收益率约 5.15%（+3bp）。盘前报价：QQQ 约 714.01（较昨收 725.20 跌 1.54%），SMH 约 538.36（较昨收 556.70 跌 3.29%）。broker 中的估值价格仍是 stale 的旧价，账户净值约 100,341.65，实际应低于此值。来源：[Yahoo：Nasdaq Futures Slide Premarket](https://finance.yahoo.com/markets/stocks/articles/nasdaq-futures-slide-premarket-ai-111659890.html)、[Yahoo：Why Are Nasdaq Futures Falling](https://finance.yahoo.com/markets/stocks/articles/why-nasdaq-futures-falling-premarket-085201550.html)、[Sunday Guardian 道指期货](https://sundayguardianlive.com/business/dow-jones-futures-today-trading-lower-056-to-068-amid-multi-day-tech-led-rally-major-corporate-earnings-escalating-geopolitical-tensions-check-key-drivers-what-investors-must-know-310203)、Yahoo 报价页（QQQ/SMH）。
- 当前策略及主要理由：适度降低科技和半导体敞口，暂不全面撤退。持仓中科技 beta 偏高（QQQ 约 40%、SMH 约 17%），AI 资本开支担忧、油价冲击、美债收益率上行和下周 FOMC 叠加，下行风险加大。计划卖出一半 SMH（15 股，限价 536，低于盘前价，大概率可以立即成交）。QQQ 卖出 10 股，限价 716.50，略高于盘前价，等反弹时成交。保留 SPY、其余 QQQ/SMH 和 XLE；XLE 受益于油价上涨，可以对冲。
- 主要风险：跳空低开后在低位卖出，如果盘中 V 型反弹会错过回升；如果抛售加剧，剩余科技仓位仍会继续亏损。

### 资金与持仓检查

- `cash.available`：2534.6000
- 主方案买入资金需求：0.00（只有卖单）
- Backup 1 买入资金需求：0.00（只有卖单）
- Backup 2 买入资金需求：未提供，0.00
- 预计冻结现金：0.00（broker 返回冻结现金 0）
- 卖出数量检查：主方案卖出 SMH 15 股，不超过 available_quantity 30；卖出 QQQ 10 股，不超过 55。Backup 1 卖出 SMH 15 股，不超过 30。broker 冻结股份 QQQ 10、SMH 15（跨候选取最大值）

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000003
  - 有效时间：2026-10-22T08:33:00-04:00 至 2026-10-22T12:00:00-04:00
  - broker 整体结果：ok=true，状态 pending。提交后 status 确认方案在 open_plans 中，冻结股份 QQQ 10、SMH 15。尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：卖出
      - 标的：SMH
      - 数量：15
      - 限价：536.00
      - 订单 ID：ord_000009
    - 订单：
      - 操作：卖出
      - 标的：QQQ
      - 数量：10
      - 限价：716.50
      - 订单 ID：ord_000010

  - Backup 1：
    - broker 状态：accepted
    - 拒绝原因：不适用
    - 订单：
      - 操作：卖出
      - 标的：SMH
      - 数量：15
      - 限价：528.00
      - 订单 ID：ord_000011

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：12:00 结算后，确认 SMH/QQQ 卖单是否成交及成交价。观察盘中能否从低开中修复、油价和伊朗局势、美债收益率，以及 8:30 公布的初请数据。卖出得到的现金（约 8k–15k）可考虑加到 XLE 或 GLD，或者等科技股企稳后再买回。
- 改变当前判断的条件：盘中收复大部分跌幅、AI 股企稳，则考虑把 SMH/QQQ 买回；抛售加剧（QQQ 跌超 2.5%）或中东冲突升级，则进一步减仓 QQQ/SPY，提高现金或能源仓位；油价急跌，则重新评估 XLE。

## 2026-10-22T15:33:11.370448-04:00

### 本轮判断

- 市场与关键信息：plan_000003 的主方案部分成交。SMH 卖出 15 股，现金从 2534.60 增至 10582.33，折合成交均价约 536.52；QQQ 卖单（限价 716.50）没有成交，到期失效；backup 随主方案被选中而失效。（12:05 那一轮因会话中断，没有提交操作，也没有留下记录。）截至 15:32，QQQ 704.03（较昨收 725.20 约 -2.9%），SMH 523.60（约 -5.9%），SPY 762.72，XLE 67.495。账户净值 97,791.03（-2.21%）。科技和半导体股因 AI 资本开支担忧继续承压，油价因伊朗局势维持高位。本轮没有搜到 10/22 下午的市场报道（结果都是其他日期的旧文，例如 [Yahoo 3/30 报道](https://finance.yahoo.com/markets/stocks/articles/stock-market-today-march-30-214657102.html)、[Argaam 科技股抛售报道](https://www.argaam.com/en/reports/international_market_daily_report/59938)）。价格以 broker 的 fresh 报价为准。
- 当前策略及主要理由：持有现有仓位（QQQ 55、SPY 40、SMH 15、XLE 150），保留约 10.6k 现金（约 11%）。上午卖出一半 SMH 的价格高于现价约 2.5%，降低风险的效果已经体现。今天科技股跌幅较大，但还不足以确认趋势反转，尾盘追跌卖出的风险/收益不划算；下周有 FOMC，油价也处高位，这时用现金抄底也偏早。今天卖出过 SMH，按规则今天不能再买入 SMH。
- 主要风险：AI 资本开支担忧可能演变成上周那样的连续下跌；伊朗、沙特局势升级可能推动油价继续上涨、美债收益率突破 5.2%，压制估值；下周 FOMC 偏鹰。

### 资金与持仓检查

- `cash.available`：10582.3250
- 主方案买入资金需求：0.00（未提交）
- Backup 1 买入资金需求：0.00（未提交）
- Backup 2 买入资金需求：0.00（未提交）
- 预计冻结现金：0.00
- 卖出数量检查：没有卖单。当前 available_quantity 为 QQQ 55、SPY 40、SMH 15、XLE 150

### 本轮操作

- 不操作：
  - 原因：上午已经卖出一半 SMH 降低风险，剩余仓位与 11% 的现金比较均衡。尾盘接近当日低位，此时追跌卖出或抄底都缺乏把握。等盘后消息（隔夜财报、中东局势）和明天盘前走势再决定。

### 后续计划

- 下轮重点检查：19:00 查看盘后财报、油价和伊朗局势新闻，以及 QQQ/SMH 的盘后价格。明早 08:30 结合期货、10 年期美债收益率和 Brent 价格，决定是否用现金逢低加仓 QQQ/SPY、增配能源或黄金，或者继续减仓。
- 改变当前判断的条件：QQQ 再跌超 2%（低于约 690）且没有企稳迹象，或者中东发生实际军事冲突，则进一步减仓 QQQ/SMH，提高现金和能源仓位；市场明显反弹、AI 股企稳，则用现金加仓 QQQ，或买回 SMH；Brent 跌破 $100，则考虑卖出 XLE。

## 2026-10-22T19:03:03.920891-04:00

### 本轮判断

- 市场与关键信息：今天科技股大跌。QQQ 收 704.47（-2.86%），盘后约 703.40（-0.15%），盘后基本企稳。SMH 收约 523.35，SPY 约 764.12，XLE 约 67.57。下跌原因是市场对 AI 支出的担忧加剧：MRVL、AMD 跌约 8%，INTC 跌约 7%，光通信股跌幅达两位数；META 跌约 3%，因为更高的资本开支指引盖过了业绩超预期；TSLA 跌约 4%。盘后没有搜到重要大盘股财报；MarketChameleon 显示 RHI +12.2%、CCI +8.7%。账户净值约 97,885.33（-2.11%）。来源：Yahoo QQQ 报价页及相关新闻标题、[MarketChameleon 盘后交易](https://marketchameleon.com/Reports/AfterHoursTrading)、[Chartmill 盘后异动](https://www.chartmill.com/news/DECK/Chartmill-56681-Postmarket-Movers-After-Hours-Gainers-and-Decliners)、[StockAnalysis 盘后](https://stockanalysis.com/markets/afterhours/)。
- 当前策略及主要理由：继续持有 QQQ 55、SPY 40、SMH 15、XLE 150，现金约 10.6k（约 11%）。今天大跌后盘后已企稳；科技股连续两天剧烈波动后，在盘后流动性差的时段卖出或买入都不划算。今天已卖出 SMH，按规则今天不能再买入 SMH。明早根据期货和油价再决定是加仓还是减仓。
- 主要风险：AI 板块的抛售可能延续，类似上周的走势；中东局势可能推动油价和美债收益率继续上行；下周 FOMC。

### 资金与持仓检查

- `cash.available`：10582.3250
- 主方案买入资金需求：0.00（未提交）
- Backup 1 买入资金需求：0.00（未提交）
- Backup 2 买入资金需求：0.00（未提交）
- 预计冻结现金：0.00
- 卖出数量检查：没有卖单。available_quantity 为 QQQ 55、SPY 40、SMH 15、XLE 150

### 本轮操作

- 不操作：
  - 原因：盘后 QQQ 只小幅波动（-0.15%），没有重要新消息。19:00–20:00 的盘后时段流动性差，此时交易不划算。明早 08:30 根据期货、油价和美债收益率再决定是否加仓 QQQ/SPY，或继续降低科技敞口。

### 后续计划

- 下轮重点检查：明早 08:30 查看纳指和标普期货、Brent/WTI、10 年期美债收益率、伊朗和沙特局势新闻，以及 10/23 盘前财报和半导体股的盘前表现。
- 改变当前判断的条件：期货明显反弹（纳指 +1% 以上）、AI 股企稳，则用部分现金加仓 QQQ，或买回 SMH；期货继续下跌超过 1%，或中东冲突升级，则进一步减仓 QQQ/SMH；Brent 跌破 $100，则考虑卖出 XLE。
