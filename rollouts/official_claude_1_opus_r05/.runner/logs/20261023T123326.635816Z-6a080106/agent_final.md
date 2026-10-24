## 2026-10-23T08:33:26.607069-04:00

### 本轮判断

- 市场与关键信息：昨天科技股大跌，QQQ 收 704.47（-2.86%）。今天盘前跌势放缓：标普期货约 -0.2% 至 -0.3%，纳指 100 期货约 -0.1%，道指期货约 -0.6% 至 -0.8%。QQQ 盘前约 703.18（-0.18%），SMH 约 524.85（+0.29%），META 和 NVDA 盘前反弹。市场仍在担心 AI 基础设施的融资问题；WTI 约 $100.9（+1.4%）；法国国债市场动荡。盘前个股：WDC 业绩超预期，但因 AI 资本需求担忧下跌约 4.5%；AXP -2.5%；RHI +10%；CCI +7.5%（与 SpaceX 洽谈基站租用）。账户净值约 97,885（以 stale 价格估算）。来源：[Investing.com 盘前异动](https://www.investing.com/news/stock-market-news/premarket-movers-crown-castle-jumps-75-on-spacex-talks-autoliv-slides-4969100)、[CNBC 直播](https://www.cnbc.com/2026/10/22/stock-market-today-live-update.html)、[Stocktwits](https://stocktwits.com/news-articles/markets/equity/nasdaq-dow-s-and-p-500-futures-drop-premarket-nvda-amd-meta-crwv-mrna-wdc-be-in-focus/cZxyfNARBxI)、Yahoo 报价页（QQQ/SMH）。
- 当前策略及主要理由：继续持有 QQQ 55、SPY 40、SMH 15、XLE 150。另挂一个 QQQ 逢低买单：14 股，限价 695.00，比盘前价低约 1.2%。今天如果盘中再跌，就在更低位置加仓；如果不跌，订单不成交，保留现金。两天累计回调约 3% 后，适度在低位加仓的期望收益为正；限价比现价低，可以避免追高。
- 主要风险：AI 板块抛售可能演变为更深的回调，即使在 695 买入也可能继续亏损；油价超过 $100、10 年期美债收益率约 5.15%，加上下周 FOMC，宏观压力仍在。

### 资金与持仓检查

- `cash.available`：10582.3250（提交前）
- 主方案买入资金需求：14×695.00 = 9730.00
- Backup 1 买入资金需求：未提供，0.00
- Backup 2 买入资金需求：未提供，0.00
- 预计冻结现金：9730.00。broker 返回冻结现金 9730.00，提交后 available 为 852.3250
- 卖出数量检查：没有卖单，不适用。available_quantity 为 QQQ 55、SPY 40、SMH 15、XLE 150

### 本轮操作

- 提交交易方案：
  - 方案 ID：plan_000004
  - 有效时间：2026-10-23T08:34:00-04:00 至 2026-10-23T12:00:00-04:00
  - broker 整体结果：ok=true，状态 pending。提交后 status 确认方案在 open_plans 中，冻结现金 9730.00。尚无成交。

  - 主方案：
    - broker 状态：accepted
    - 订单：
      - 操作：买入
      - 标的：QQQ
      - 数量：14
      - 限价：695.00
      - 订单 ID：ord_000012

  - Backup 1：
    - broker 状态：未提供
    - 拒绝原因：不适用

  - Backup 2：
    - broker 状态：未提供
    - 拒绝原因：不适用

### 后续计划

- 下轮重点检查：12:00 结算后，确认 QQQ 逢低买单是否成交。观察盘中科技股能否企稳、油价和美债收益率，以及法国国债市场的影响。如果买单成交，今天不能再卖出 QQQ。
- 改变当前判断的条件：QQQ 跌破约 690 且没有企稳迹象，或中东冲突升级，则停止加仓，并考虑明天减仓 SMH/QQQ；科技股强劲反弹，则继续持有，未成交的现金留待下次回调时使用；Brent 跌破 $100，则考虑卖出 XLE。