# 模拟券商规则（Protocol v1.1）

## 协议版本

- `v1.1` 自 `2026-10-22 12:00 America/New_York` 的结算起生效，不回算或改写此前的账户状态、订单或成交。
- 本次修订只增加决策前持仓估值刷新，以及盘前盘后整单成交的分钟成交量门槛；常规时段的限价触发规则不变。

## 账户

- 初始现金为 99948.5000 美元，所有金额以美元计。
- 只能交易 `universe.txt` 中的证券，并以现金建立整数股多头持仓；不允许融资、直接卖空、期权或零股。
- `universe.txt` 中列出的反向 ETF 和杠杆 ETF 可以买入，例如 `SOXS`；产品自身的反向或杠杆敞口不视为账户融资或直接卖空。
- 佣金为 0；买入占用现金，卖出占用持仓，已被挂单占用的资金或股份不能重复使用。
- 账户净值、持仓、订单和成交记录以模拟券商账本为准，不得直接修改账本。

## 交易时间与方案

- 所有时间均为美国东部时间。交易日按美股官方日历确定，闭市或停牌期间不成交。
- 只接受限价单，不接受市价单。
- 每次决策最多提交一个交易方案。一个交易方案包含一个主方案和最多两个有固定优先级的 backup 方案；每个候选方案都可以包含任意数量的限价单。
- broker 为交易方案设置 `valid_from` 和 `valid_until`。候选订单只可在 `[valid_from, valid_until)` 内触发，窗口结束后不再继续挂单。
- 每日 Agent 唤醒时间为 `08:30`、`12:00`、`15:30`、`19:00`；broker 的方案截止边界依次为 `12:00`、`15:30`、`19:00`、`20:00`。无论实际命令在窗口内何时到达，`valid_until` 都取严格晚于 `valid_from` 的下一个截止边界。

## 延迟撮合

- 撮合由确定性的程序执行，不使用语言模型，也不需要实时运行行情 tracker。
- 每次执行 `./broker status`、`submit-plan` 或 `cancel` 时，程序先结算所有截至当前命令接收时间已经到期的交易方案，再处理当前命令。尚未到达 `valid_until` 的方案保持待结算状态。
- runner 可以在窗口边界到达且 Yahoo 已有完整数据后执行 `./broker settle --json`，再唤醒 Agent。不得在 `valid_until` 之前提前结束方案；`status`、`submit-plan` 和 `cancel` 仍保留自动结算作为兜底。
- 每次结算把该方案所有已接受候选涉及的 ticker 合并到一次 Yahoo 批量请求。正常成功路径只调用一次；缓存命中时不调用。请求失败可以整批重试，但不得拆成逐 ticker 轮询。
- 第一阶段唯一行情源为 Yahoo Finance，通过实验开始前固定版本的 `yfinance` 获取。该数据仅用于本地、非实盘的研究实验。
- 行情请求固定使用 `interval="1m"`、`prepost=True`、`auto_adjust=False`、`actions=True`、`keepna=True`；不得依赖这些参数的库默认值。
- 所有轨迹使用同一份未复权 1 分钟 OHLCV 和盘前盘后数据。每批缓存同时保存获取时间、请求区间、请求参数、`yfinance` 版本和内容校验信息。
- Yahoo/Pandas 返回的二进制浮点 OHLC 在进入缓存前统一使用 half-even 规则转换为小数点后 4 位十进制定点数，避免浮点尾差影响现金、成本和复现结果。
- 候选订单从交易方案提交后的下一根完整 1 分钟 K 线开始生效，不得使用提交前或提交当分钟已经出现的价格。
- 只使用 08:00–20:00 内且成交量大于 0 的 K 线判断成交。
- 在常规时段 `09:30–16:00`，继续按价格触发规则整单成交，不额外用分钟成交量限制订单数量。
- 在盘前 `08:00–09:30` 和盘后 `16:00–20:00`，价格满足条件之外，触发 K 线的成交量还必须大于或等于该笔订单数量；不足时跳过该 K 线，继续寻找下一根同时满足价格和成交量条件的 K 线。仍不做部分成交。

买入限价单按以下规则判断：

- 若某根有效 K 线的开盘价不高于限价，按开盘价成交。
- 否则，若该 K 线的最低价不高于限价，按限价成交。

卖出限价单按以下规则判断：

- 若某根有效 K 线的开盘价不低于限价，按开盘价成交。
- 否则，若该 K 线的最高价不低于限价，按限价成交。

通用成交规则：

- 按时间顺序找到的第一根满足条件的 K 线即为触发 K 线，成交时间记录为该 K 线的时间。
- 触发后整单成交，不模拟盘口深度、排队顺序或部分成交；成交价格不得差于订单限价。盘前盘后另受上述触发 K 线成交量门槛约束。
- 同一候选方案内多个订单在同一根 K 线触发时，按订单 ID 依次处理。
- 撤销方案时先把当前命令接收时间作为该方案的新 `valid_until` 并执行结算；若方案已经选中并产生成交则撤销失败，否则撤销成功。
- Yahoo 成功响应但个别 K 线缺失、成交量为 0 或字段无效时，该分钟不成交，并将数据缺口记入缓存。
- 整批行情请求失败时可以重试；仍然失败则不得推进结算游标，也不得处理新的下单或撤单操作，并返回 `MARKET_DATA_UNAVAILABLE`。不得切换其他行情源静默补数。
- 每笔成交保存触发 K 线的 OHLCV、行情时间戳、Yahoo 获取时间、请求参数、`yfinance` 版本和缓存校验信息，供事后审计与复现。
- 拆股、合并和现金分红由券商自动处理。

## 主方案与 backup 选择

- 主方案的订单数量不设人为上限；每个 backup 方案的订单数量同样不设人为上限。
- backup 方案最多两个，固定按 `backup 1`、`backup 2` 排序。少于两个时允许省略。
- 方案到期后，matcher 先在完整有效时间段内模拟主方案的所有订单。只要主方案至少有一笔订单可以成交，就选中主方案，所有 backup 立即失效。
- 只有主方案零成交时才检查 `backup 1`；只有 `backup 1` 零成交或在提交时被拒绝时才检查 `backup 2`。
- 选中某个候选方案后，该候选中所有能成交的订单均按各自第一根满足条件的 K 线成交；未成交订单随交易方案一同到期。
- 主方案和 backup 不得混合成交。一个交易方案最多选中一个候选方案；三个候选均零成交时，交易方案状态变为 `expired`。
- 候选方案及其优先级必须在 `valid_from` 之前固定。matcher 不得根据事后收益、收盘价格或其他结果挑选候选方案。

## 日内交易限制

- 同一证券在同一交易日一旦发生买入成交，当日不得卖出；一旦发生卖出成交，当日不得买入。
- 每个候选方案独立校验日内方向限制；同一候选方案内不得同时买入和卖出同一证券。不同候选方案之间可以表达不同方向，因为最终只会选择一个候选。
- 该限制在下一个交易日重置。主方案违反规则时拒绝整个提交；backup 违反规则时只拒绝该 backup。

## 状态、冻结与审计

- 每条轨迹拥有完全独立的 `state.json` 和 `ledger.jsonl`，不得读取其他轨迹的文件。
- `state.json` 是当前账户快照，保存现金、持仓、待结算交易方案、订单序号和行情结算游标；只有 broker 程序可以更新，Agent 不得直接读取、修改或替换该文件。
- `ledger.jsonl` 是只追加的审计流水，逐行记录账户初始化、方案提交、候选接受或拒绝、方案选择、方案到期或撤销、成交、估值刷新和公司行动；已有记录不得修改或删除。
- broker 更新状态时必须先写入同目录临时文件，再以原子替换方式更新 `state.json`。只有状态和审计记录提交成功后，命令才可返回成功。
- 主方案和每个 backup 使用同一份提交前账户快照分别校验，不把其他候选方案的资源冻结视为已占用。
- Agent 在决策记录或 `PLAN.json` 中提供的预算数字仅用于说明，不能作为校验依据；broker 必须根据 `cash.available`、`positions[].available_quantity`、订单数量和限价独立重新计算。
- 主方案必须独立满足全部规则。主方案资金不足、持仓不足或含有无效订单时，拒绝整个交易方案。
- 某个 backup 资金不足、持仓不足或含有无效订单时，只拒绝该 backup；主方案和其他有效 backup 仍然接受。返回结果必须逐个写明 `accepted` 或 `rejected` 及原因。
- 每个候选方案的买入资金需求等于其中所有买单的 `数量 × 限价` 之和，且不得超过提交时的可用现金。
- 没有买单的候选方案买入资金需求记为 `0.00`。所有乘法和加法均使用十进制定点数，不使用二进制浮点数。
- 不能假设卖单先成交，也不能使用预计卖出所得为同一候选方案的买单提供资金。
- 每个候选方案按证券汇总卖出数量，均不得超过提交时该证券的可用持仓；不允许融资、透支或负持仓。
- 接受交易方案后，冻结现金等于所有已接受候选方案各自买入资金需求的最大值，而不是候选方案资金需求之和。
- 对每个证券，冻结股份等于所有已接受候选方案中该证券卖出数量的最大值，而不是跨候选方案相加。
- 候选方案成交时按真实成交价扣减现金或股份，并释放整套交易方案剩余的冻结资源；方案到期或成功撤销时释放全部冻结资源。
- `cash.total` 包含已冻结现金，`cash.available = cash.total - cash.reserved`。
- `positions[].quantity` 包含已冻结股份，`available_quantity = quantity - reserved_quantity`。
- 撮合时只请求待结算交易方案中所有已接受候选订单涉及的标的。每次唤醒 Agent 前，runner 另将该账户全部持仓标的合并成一个估值批次，从当日 `08:00` 请求到当前最新完整分钟，并使用各标的最新有效收盘价更新市值；该估值批次不得用于补做或改变订单成交。同一 ticker 和时间区间只下载一次，所有轨迹共用只读行情缓存，但不共用账户状态。
- 行情批次一旦被任何轨迹用于撮合即成为不可变记录，后续下载不得覆盖；若 Yahoo 返回不同数据，只记录冲突并继续使用首次用于撮合的版本。

## 操作接口

所有命令都以 JSON 输出结果。命令成功时退出码为 `0`；参数错误、订单被拒绝或撤单失败时退出码非 `0`，但仍必须向标准输出返回合法 JSON。时间均使用带 UTC 偏移量的美东时间 ISO 8601 字符串，金额和价格统一使用十进制定点数记账，并以字符串输出。

### Runner 预结算

每个决策边界到达后，runner 应先等待行情源产生最后一根完整 K 线，再执行：

```bash
./broker settle --json
./broker refresh-valuation --json
```

`settle` 只结算已经到达 `valid_until` 的方案，不会提前终止尚未到期的方案，也不会提交新交易。`refresh-valuation` 批量刷新当前全部持仓的估值，不参与撮合。推荐顺序为：

```text
窗口边界到达 → 等待 Yahoo 数据可用 → settle → refresh-valuation → 唤醒 Agent → Agent 执行 status
```

具体等待时间应在 pilot 中根据 Yahoo 实际延迟固定；不能为了准点唤醒而省略有效区间末尾的 K 线。

### 查看状态

查看账户、持仓和待结算交易方案：

```bash
./broker status --json
```

调用时先完成延迟撮合，再返回如下结构：

```json
{
  "ok": true,
  "command": "status",
  "as_of": "2026-10-19T10:30:00-04:00",
  "settled_through": "2026-10-19T10:29:00-04:00",
  "account": {
    "initial_cash": "100000.00",
    "cash": {
      "total": "75000.00",
      "reserved": "10000.00",
      "available": "65000.00"
    },
    "positions_market_value": "25500.00",
    "equity": "100500.00",
    "valuation_status": "fresh",
    "valuation_errors": []
  },
  "positions": [
    {
      "symbol": "QQQ",
      "quantity": 50,
      "reserved_quantity": 0,
      "available_quantity": 50,
      "average_cost": "500.00",
      "latest_price": "510.00",
      "latest_price_at": "2026-10-19T10:29:00-04:00",
      "price_source": "yahoo_finance",
      "price_status": "fresh",
      "market_value": "25500.00",
      "unrealized_pnl": "500.00"
    }
  ],
  "open_plans": [
    {
      "plan_id": "plan_000001",
      "submitted_at": "2026-10-19T08:03:21-04:00",
      "valid_from": "2026-10-19T08:04:00-04:00",
      "valid_until": "2026-10-19T12:00:00-04:00",
      "status": "pending",
      "primary": {
        "status": "accepted",
        "orders": [
          {
            "order_id": "ord_000001",
            "symbol": "SPY",
            "side": "buy",
            "quantity": 20,
            "limit_price": "500.00"
          }
        ]
      },
      "backups": [
        {
          "priority": 1,
          "status": "accepted",
          "orders": [
            {
              "order_id": "ord_000002",
              "symbol": "QQQ",
              "side": "buy",
              "quantity": 10,
              "limit_price": "480.00"
            }
          ]
        },
        {
          "priority": 2,
          "status": "rejected",
          "orders": [],
          "error": {
            "code": "INSUFFICIENT_CASH",
            "message": "backup exceeds available cash"
          }
        }
      ]
    }
  ],
  "fills": []
}
```

- `as_of` 是 broker 接收当前命令的时间；`settled_through` 是已完成回放的最后一根 K 线时间。
- `open_plans` 展示尚未到达 `valid_until` 的交易方案以及每个候选的接受状态。
- `fills` 只包含当前命令开始时完成方案选择后新产生的成交；完整历史以 `ledger.jsonl` 为准。
- `equity = cash.total + positions_market_value`。估值优先使用截至 `as_of` 的最新有效 Yahoo 价格。
- 当前可用价格距 `as_of` 不超过 5 分钟时，`price_status` 为 `fresh`；否则可以使用最近的缓存价格估值，但必须返回 `stale`。过期价格只能估值，不能撮合。
- `valuation_status` 为 `fresh`、`stale` 或 `incomplete`：全部持仓价格新鲜时为 `fresh`，任一持仓使用过期价格时为 `stale`；任一持仓从未取得有效价格时为 `incomplete`，对应价格、市值、总持仓市值和账户净值返回 `null`，并在 `valuation_errors` 中列明标的与原因。

### 提交交易方案

主方案和最多两个 backup 必须在一次命令中原子提交：

```bash
./broker submit-plan --file PLAN.json --json
```

`PLAN.json` 格式如下。`valid_from` 和 `valid_until` 由 broker 根据提交时间及下一决策窗口写入，Agent 不得自行指定：

```json
{
  "primary": {
    "orders": [
      {
        "symbol": "SPY",
        "side": "buy",
        "quantity": 20,
        "limit_price": "500.00"
      }
    ]
  },
  "backups": [
    {
      "orders": [
        {
          "symbol": "QQQ",
          "side": "buy",
          "quantity": 10,
          "limit_price": "480.00"
        }
      ]
    },
    {
      "orders": [
        {
          "symbol": "NVDA",
          "side": "buy",
          "quantity": 1000,
          "limit_price": "180.00"
        }
      ]
    }
  ]
}
```

broker 先结算已经到期的旧方案，再根据结算后的账户快照分别校验主方案和两个 backup。主方案有效、backup 2 超出余额时，返回示例：

```json
{
  "ok": true,
  "command": "submit-plan",
  "as_of": "2026-10-19T08:03:21-04:00",
  "settled_through": "2026-10-19T08:02:00-04:00",
  "plan": {
    "plan_id": "plan_000001",
    "submitted_at": "2026-10-19T08:03:21-04:00",
    "valid_from": "2026-10-19T08:04:00-04:00",
    "valid_until": "2026-10-19T12:00:00-04:00",
    "status": "pending",
    "primary": {
      "status": "accepted",
      "orders": [
        {
          "order_id": "ord_000001",
          "symbol": "SPY",
          "side": "buy",
          "quantity": 20,
          "limit_price": "500.00"
        }
      ]
    },
    "backups": [
      {
        "priority": 1,
        "status": "accepted",
        "orders": [
          {
            "order_id": "ord_000002",
            "symbol": "QQQ",
            "side": "buy",
            "quantity": 10,
            "limit_price": "480.00"
          }
        ]
      },
      {
        "priority": 2,
        "status": "rejected",
        "orders": [],
        "error": {
          "code": "INSUFFICIENT_CASH",
          "message": "required cash exceeds available cash",
          "details": {
            "required": "180000.00",
            "available": "100000.00"
          }
        }
      }
    ]
  },
  "reservation": {
    "cash": "10000.00",
    "positions": {}
  },
  "fills": []
}
```

只要主方案被接受，命令就返回 `"ok": true`。被拒绝的 backup 不生成订单 ID，也不影响主方案或其他有效 backup。若 `backup 1` 被拒绝，方案到期时可在主方案零成交后直接检查已接受的 `backup 2`。

同一轨迹同一时间只允许一个待结算交易方案。主方案无效、backup 超过两个或提交结构无效时，整个命令失败且不生成方案 ID。

### 撤销交易方案

只能整体撤销尚未结算的交易方案，不能单独撤销其中一笔候选订单：

```bash
./broker cancel PLAN_ID --json
```

broker 将命令接收时间作为方案的新 `valid_until` 并先执行方案选择。若截至该时间三个候选均零成交，撤销成功并释放冻结资源：

```json
{
  "ok": true,
  "command": "cancel",
  "as_of": "2026-10-19T10:00:03-04:00",
  "settled_through": "2026-10-19T09:59:00-04:00",
  "plan": {
    "plan_id": "plan_000001",
    "status": "cancelled",
    "cancelled_at": "2026-10-19T10:00:03-04:00"
  },
  "released": {
    "cash": "10000.00",
    "positions": {}
  },
  "fills": []
}
```

若结算后已有候选方案产生成交，则方案状态变为 `selected`，撤销失败并返回 `PLAN_NOT_OPEN`。

### 错误格式

所有失败统一返回：

```json
{
  "ok": false,
  "command": "submit-plan",
  "as_of": "2026-10-19T11:00:05-04:00",
  "settled_through": "2026-10-19T10:59:00-04:00",
  "error": {
    "code": "INSUFFICIENT_CASH",
    "message": "available cash is lower than the required reservation",
    "details": {
      "required": "10000.00",
      "available": "9000.00"
    }
  },
  "fills": []
}
```

固定错误码如下：

- `INVALID_ARGUMENT`：参数缺失、类型错误、数量不是正整数或价格无效。
- `SYMBOL_NOT_ALLOWED`：标的不在 `universe.txt`。
- `MARKET_DATA_UNAVAILABLE`：整批 Yahoo 行情请求在重试后仍失败，不能安全推进结算游标或处理交易操作。
- `INSUFFICIENT_CASH`：候选方案的买入资金需求超过可用现金；发生在 backup 时只拒绝该 backup。
- `INSUFFICIENT_POSITION`：候选方案的卖出数量超过可用持仓；发生在 backup 时只拒绝该 backup。
- `DAY_TRADE_RESTRICTED`：候选方案违反同一交易日的方向限制；发生在 backup 时只拒绝该 backup。
- `CONFLICTING_ORDERS`：同一候选方案内包含同一证券的相反方向订单。
- `TOO_MANY_BACKUPS`：提交了超过两个 backup，整个命令失败。
- `ACTIVE_PLAN_EXISTS`：当前已有尚未结算的交易方案。
- `PLAN_NOT_FOUND`：方案 ID 不存在于当前轨迹。
- `PLAN_NOT_OPEN`：方案已经选中、到期或撤销，不能再次撤销。
- `STATE_CONFLICT`：状态版本冲突或并发更新失败。
- `INTERNAL_ERROR`：未归类的内部错误；公开响应不得包含密钥或其他轨迹的信息，完整诊断只追加到当前轨迹私有的 `.broker/internal_errors.jsonl`。

只有 `./broker` 返回 `"ok": true` 时交易方案才成立；仍须逐项读取 backup 的 `status`，被拒绝的 backup 不具有任何交易效力。不提供原地修改方案的接口。
