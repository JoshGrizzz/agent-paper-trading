# 实时模拟交易 Agent 实验

## 目标

比较不同模型及其原生 coding-agent harness 在真实市场环境中进行自主交易的能力，重点观察：

1. Agent 能否在极少提示下自主获取信息、决定交易，并根据后续反馈调整。
2. 更强或更贵的模型是否产生更好的真实世界结果。

只使用实验开始后的实时信息和实时行情，避免历史回测的数据泄漏。当前先做 zero-shot 交易；Agent 自主编写研究或交易程序的实验留到下一阶段。

## 固定实验规则

- 市场：美股虚拟盘，按统一的真实行情模拟成交，不使用真钱。
- 初始资金：每条轨迹独立拥有 100,000 美元。
- 交易范围：只能交易冻结后的 `universe.txt` 白名单。
- 订单类型：只允许限价单，不允许市价单。
- 每轮可以提交一个主方案和最多两个有固定优先级的 backup 方案；每个候选方案可包含任意数量的限价单。
- 主方案任意一笔成交即选中主方案；只有当前候选零成交才检查下一 backup，且一个交易方案最多选择一个候选。
- 仓位：不设置“单笔订单不得超过账户净值某一比例”的额外限制，仍须满足现金、持仓和 `BROKER.md` 中的其他规则。
- 决策窗口：每个美股交易日于美东时间 `08:30`、`12:00`、`15:30`、`19:00` 唤醒。
- 时区：调度统一使用 `America/New_York`，自动处理夏令时，不使用固定 UTC 偏移量。
- `08:30` 属于盘前，`19:00` 属于盘后；有效限价单可按 `BROKER.md` 在 `08:00–20:00` 的有效行情中触发成交。
- 每次唤醒后由 broker 懒加载并回放所需的 1 分钟 K 线，不运行逐分钟行情 tracker。
- 实际唤醒顺序为“窗口边界到达、等待 Yahoo 返回完整 K 线、runner 执行 `./broker settle --json`、执行 `./broker refresh-valuation --json`、再启动 Agent”。不得在旧方案 `valid_until` 之前预结算。估值刷新将全部现有持仓按截至当前最新完整分钟的 Yahoo 盘前、盘中或盘后价格统一更新，但不参与订单撮合。
- 一次结算把方案涉及的全部 ticker 合并为一次 Yahoo 批量调用；共享缓存命中时不再调用 Yahoo。
- 第一阶段唯一行情源为 Yahoo Finance，通过 `yfinance` 获取；仅用于本地、非实盘的研究实验，不对外分发原始行情。
- pilot 开始前固定 `yfinance` 版本，并将版本与请求参数写入运行清单。
- 每个模型配置运行 5 条相互独立的 rollout；稳定运行一周后再考虑增加到 10 条。
- 首轮优先使用各产品订阅额度，不使用模型 API。

## 候选模型与 harness

- OpenAI：GPT-5.6 Sol、GPT-5.6 Luna、GPT-6 Sol、GPT-6 Luna + Codex。
- Anthropic：Claude Opus 5.5、Sonnet 5.5、Haiku 5.5 + Claude Code。
- 中国模型：GLM + ZCode；DeepSeek + DSH。具体模型档位和可用并发仍需在 pilot 前确认。

一个正在执行的 rollout 占用一个并发槽。模型名称、harness 版本、订阅档位和实际并发上限必须在实验开始前冻结并写入运行清单。

## 轨迹隔离

每条轨迹拥有独立工作目录和独立账户，只能访问：

- 共享只读的 `BROKER.md`、`universe.txt` 和 `DECISION_FORMAT.md`。
- 该轨迹自己的原生 harness session、`DECISIONS.md`、`state.json`、`ledger.jsonl`、运行日志和原始模型输出。
- 公共互联网与该轨迹通过 `./broker` 获得的账户信息。

任何轨迹都不得读取其他轨迹的决策、账户、订单、成交或模型输出。Agent 不得直接读取或修改 `state.json` 和 `ledger.jsonl`，只能通过 `./broker` 查看账户、下单和撤单。

默认禁用模型或 harness 自行创建子 Agent、并行 Agent 或委派任务的能力，避免不同产品因内部并发能力不同而获得额外优势。

## 调度与并发

每个决策窗口包含 5 个顺序执行的波次。每个波次对每个模型配置最多启动 1 条 rollout，因此同一模型配置不会同时运行自己的两条轨迹。

同一波次内的目标并发为：

- OpenAI/Codex 组：5 个模型配置并发。
- Anthropic/Claude Code 组：3 个模型配置并发。
- ZCode 与 DSH：分别按 pilot 实测和订阅限制设置；未确认前采用保守并发。
- runner 不得超过各供应商当时实际允许的并发或用量限制。

单个波次最长 15 分钟。当前波次全部完成或达到超时后才进入下一波次；超时任务应终止并记录，不得在后台与后续波次重叠。

5 条 rollout 在连续决策窗口中循环轮换波次：

| 决策窗口序号 | 波次 1 | 波次 2 | 波次 3 | 波次 4 | 波次 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | rollout 01 | rollout 02 | rollout 03 | rollout 04 | rollout 05 |
| 2 | rollout 02 | rollout 03 | rollout 04 | rollout 05 | rollout 01 |
| 3 | rollout 03 | rollout 04 | rollout 05 | rollout 01 | rollout 02 |
| 4 | rollout 04 | rollout 05 | rollout 01 | rollout 02 | rollout 03 |
| 5 | rollout 05 | rollout 01 | rollout 02 | rollout 03 | rollout 04 |

第 6 个决策窗口重新使用第 1 行，轮换跨交易日连续计算，不在每天重置。这样一周 20 个决策窗口内，每条 rollout 恰好位于每个波次 4 次，平衡因实际运行时间不同带来的市场时点偏差。

## Broker、撮合与行情

- `./broker` 是账户状态和交易操作的唯一接口；`state.json` 是内部快照，`ledger.jsonl` 是只追加审计流水。
- 每次 `status`、`submit-plan` 或 `cancel` 都先完成所有已经到期方案的选择与撮合，再处理命令。
- 撮合由统一的确定性 Python 程序完成，不由各模型自行判断是否成交。
- 主方案必须独立满足现金和持仓规则；无效 backup 只拒绝该 backup，不得导致有效主方案或其他 backup 整体作废。
- 候选方案分别校验余额。冻结现金取各已接受候选资金需求的最大值，不把互斥候选的资金需求相加；任何候选都不能贷款或依赖预计卖出所得。
- 撮合只为待结算方案中已接受候选订单涉及的标的批量获取分钟线；持仓估值只获取持仓标的的最新有效价格。
- Yahoo Finance 请求固定使用 `interval="1m"`、`prepost=True`、`auto_adjust=False`、`actions=True` 和 `keepna=True`。
- 盘前 `08:00–09:30` 和盘后 `16:00–20:00` 的整单成交要求触发 K 线成交量不少于订单数量；常规时段 `09:30–16:00` 不增加该门槛，所有时段均不模拟部分成交。
- 同一 ticker 和时间区间只下载一次，所有轨迹共享同一份只读、不可变行情缓存，但账户状态完全隔离。
- 已用于撮合的 K 线不得被后续重新下载的数据覆盖；缓存保存获取时间、请求参数、`yfinance` 版本和校验信息。
- 请求失败时允许重试，但不使用其他行情源静默补数。没有可靠 K 线时不成交，也不猜测价格。
- 若 Yahoo 暂时未提供最新盘前或盘后价格，估值可使用最近的缓存价格，但必须在 broker 输出中标记为 `stale`；过期价格不得用于撮合。
- 统一的独立评估程序从审计流水计算收益、风险、换手和违规等指标，不采用参赛 Agent 的自我评价。

### 协议修订记录

- `v1.1`：自 `2026-10-22 12:00 America/New_York` 的结算起，加入决策前全持仓实时估值刷新，以及盘前盘后触发 K 线成交量不少于整单数量的门槛。历史成交不回算；修订前的全部成交均发生于常规时段，因此没有既有成交受到新流动性规则影响。

## 决策上下文

`DECISIONS.md` 是每条轨迹自己的长期决策上下文，由 runner 在每轮结束后追加，Agent 不得修改、删除或重写历史记录。

每轮标准流程：

1. 阅读 `BROKER.md`、`universe.txt`、`DECISION_FORMAT.md` 和本轨迹的 `DECISIONS.md`。
2. 执行 `./broker status --json`，获得结算后的现金、持仓、待结算交易方案和账户净值。
3. 自主联网研究并决定提交主方案、最多两个 backup、撤销当前方案或不操作。
4. 将完整方案写入本轮 `PLAN.json`，通过 `./broker submit-plan --file PLAN.json --json` 原子提交；撤销时使用 `./broker cancel PLAN_ID --json`。
5. 提交前使用 `cash.available` 和 `positions[].available_quantity` 对每个候选方案分别做预算检查；提交后检查 broker 对主方案及每个 backup 的独立接受结果，再次执行 `./broker status --json` 确认最终账户状态。
6. 按 `DECISION_FORMAT.md` 输出且只输出一条本轮决策记录，由 runner 追加到 `DECISIONS.md`。

账户事实始终以 `./broker` 返回值为准，不能根据聊天记忆或 `DECISIONS.md` 推断成交。每条 rollout 首轮创建一个原生 harness session，后续 CLI 调用按 `.runner/session.json` 中的精确 session ID 恢复；Codex、Claude Code、DSH 和 ZCode 分别使用各自的 UUID、`session-…` 或 `sess_…` 标识。完整对话负责连续研究上下文，`DECISIONS.md` 负责精炼、可审计的长期决策记录。不得用“最近一次会话”之类的隐式选择猜测会话。

## Prompt 草案（尚未冻结）

每次唤醒均注入以下固定任务提示：

```text
你正在参加一个美股模拟交易比赛。你的目标是在比赛结束时尽可能提高账户价值。

请实际阅读当前工作目录中的 BROKER.md、universe.txt、DECISION_FORMAT.md 和 DECISIONS.md，并遵守其中的全部规则。优先使用专用文件读取工具；若没有专用读取工具但普通 shell 可用，可以使用 sed 等只读命令读取这四个文件。不得读取其他 rollout。DECISIONS.md 只包含你自己的历史决策；账户、持仓、订单和成交状态始终以 ./broker 返回的结果为准。

首先执行 ./broker status --json。你负责自主研究、决策和交易；每轮可提交一个含主方案和最多两个 backup 的限价方案，也可以撤销当前方案或不操作。只能通过 ./broker 提交或撤销方案，不得直接修改账户文件。

提交前必须使用 status 返回的 cash.available 和 positions[].available_quantity 做预算：分别计算每个候选方案全部买单的 Σ(数量 × 限价)，每个候选都必须独立负担得起；不同候选互斥，预计冻结现金取有效候选资金需求的最大值，而不是相加。不得把预计卖出收入用于支付同一候选方案的买单，也不得卖出超过 available_quantity 的股份。

完成操作后再次查看账户状态，并逐项确认主方案和每个 backup 是否被接受。你的预算仅用于决策说明，最终结果始终以 broker 的独立校验为准。

每轮结束时，最终回复必须且只能包含一条符合 DECISION_FORMAT.md 的决策记录。系统会自动将其追加到 DECISIONS.md，请不要自行修改历史记录或 `.runner`。runner 会在每轮提示词中动态给出权威时间，最终回复第一行必须严格写成 `## <本轮权威美东时间 ISO 8601>`，不得使用代码围栏；`### 本轮操作` 必须明确包含 `提交交易方案`、`撤销交易方案` 或 `不操作` 三者之一。
```

本轮消息只提供当前时间并要求继续，例如：

```text
当前时间：2026-10-19T12:00:00-04:00。继续。
```

## 手动 runner

当前阶段实现了单条 rollout runner、轻量并发连通性测试、按供应商运行的完整并发 smoke 启动器，以及 Codex、Claude Code 和 ZCode 的正式五波决策窗口调度器；尚不包含定时唤醒。单条轨迹可先初始化：

```bash
./run_rollout init --rollout rollout_01
```

随后选择原生 harness 和模型运行一轮：

```bash
./run_rollout run --rollout rollout_01 --harness codex --model MODEL_NAME --reasoning-effort high
./run_rollout run --rollout rollout_01 --harness claude --model MODEL_NAME --reasoning-effort high
./run_rollout run --rollout rollout_01 --harness dsh --model CONFIGURED_MODEL --reasoning-effort high
./run_rollout run --rollout rollout_01 --harness zcode --model CONFIGURED_MODEL --reasoning-effort high
```

Codex 和 Claude Code 的模型及推理档位由命令行直接指定。当前 DSH 和 ZCode CLI 没有等价的逐次模型/推理档位参数，因此它们的 `--model` 与 `--reasoning-effort` 只作为运行清单中的审计标签；实际模型必须先在各自原生配置中选定，并在 pilot 前单独核对、冻结。不得把审计标签误认为 CLI 已切换模型。

测试时可以使用带 UTC 偏移量的 `--as-of`，这会把权威测试时间直接写入该轮生成的 broker launcher，冻结 runner 与 Agent 发出的全部 broker 命令；冻结模式会在可用时关闭 harness 搜索工具，并明确禁止获取模拟时间之后的信息。正式运行时不传 `--as-of`，launcher 会清除继承的测试时间，各 broker 命令使用自己的实际接收时间。每轮 runner 会依次执行预结算、状态检查、一次独立 CLI 进程和事后状态检查。四种 harness 都在首轮创建持久 session，后续轮次以相同工作目录和精确 session ID 恢复；最终决策记录通过校验后再原子追加到该轨迹的 `DECISIONS.md`。决策标题必须包含合法且带偏移量的 ISO 时间，但最终保存时间统一由 runner 改写为本轮权威 `as_of`，避免恢复会话复用旧时间。若最终回复在唯一决策记录前附带普通说明，runner 会丢弃该前言并保留原始输出日志；多个决策记录和代码围栏仍会被拒绝。Agent 开始前，runner 会在预结算之后快照 `.broker/state.json` 与 `ledger.jsonl`；如果 Agent、完整性检查或决策校验失败，会保留预结算结果并回滚本轮 Agent 产生的 broker 副作用。

每条轨迹位于 `rollouts/<rollout_id>/`，账户快照位于其 `.broker/`，原生 harness session 映射位于 `.runner/session.json`，原始 harness 输出、prompt、结算结果和前后状态位于 `.runner/logs/<run_id>/`。未分类的 broker 异常会追加到该轨迹私有的 `.broker/internal_errors.jsonl`，公开 JSON 仍只返回稳定的 `INTERNAL_ERROR`。`BROKER.md`、`universe.txt` 和 `DECISION_FORMAT.md` 会在轨迹初始化时复制为轨迹内的只读规则快照，以便受限 Agent 能读取但不能修改；若项目规则后来变化，应新建 rollout，而不是静默改写既有实验。共享行情缓存仍位于项目级 `.market-cache/`。

同一个 rollout 同时只能运行一轮；重复并发会被 `.runner/run.lock` 拒绝。session 首次绑定 harness 和模型标签后，两者都不得更换。Agent 若直接修改 `DECISIONS.md`、broker launcher 或 session 映射，runner 会恢复受保护内容并将本轮标记为失败。单轮默认超时 900 秒，可用 `--timeout` 调整。

Smoke 结果分三层判断：

1. runner/transport：完成 broker 前置步骤、启动 CLI，并写出完整 stdout、stderr 和 failure 日志；
2. harness/session：CLI 退出码为 0、返回可持久化 session ID，并能用该 ID 完成第二轮恢复；
3. decision：最终回答符合固定格式并成功追加到 `DECISIONS.md`。

如果 Agent 已正常完成但因行情、冻结时间或输出格式导致第 3 层失败，仍可视为 adapter 基础 smoke 通过；认证失败、缺少 API key、CLI 非零退出或拿不到 session ID 不能视为 harness smoke 通过。

### 手动 4 并发（Codex，全 high）

先激活已安装项目依赖的环境，并用 dry-run 核对四条命令：

```bash
conda activate finance
./run_four_high --dry-run
```

确认后正式启动：

```bash
./run_four_high
```

默认同时运行 GPT-5.6 Sol、GPT-5.6 Luna、GPT-6 Sol 和 GPT-6 Luna；`manual01` rollout set 对应四个固定 rollout ID，重复执行脚本会自动续接各自原有的 Codex session、账户和决策历史。只有 batch ID 每次变化，用于把本次汇总日志写入新的 `parallel_runs/<batch_id>/`；每条 rollout 的完整日志仍写入自己的 `.runner/logs/`。四条进程全部显式设置为 `high`，单条超时 900 秒。任一任务失败时脚本等待其他任务结束后返回非零状态；按 Ctrl-C 会终止本批次的四个子进程。脚本末尾的成功只表示四个 Agent 进程和 runner 校验完成，不能替代对各 rollout summary、broker 状态及候选接受结果的检查。

新实验或不同模型组合必须选择新的 `--rollout-set`；也可用正好四个逗号分隔的模型 ID 覆盖默认组合，例如用同一模型测试四并发：

```bash
MODELS=gpt-6-luna,gpt-6-luna,gpt-6-luna,gpt-6-luna ./run_four_high --rollout-set luna01
```

`./run_four_high --rollout-set smoke01 --as-of 2026-10-19T17:00:00-04:00` 只用于冻结 broker 时间的 smoke test；正式实时实验应使用单独的 rollout set 且不得传 `--as-of`。脚本只负责一个手动并发批次，不负责决策窗口、五波轮换或跨日调度。

### 并发连通性 smoke（不交易）

`run_concurrency_smoke` 直接调用原生 CLI，只验证目标并发是否能同时完成最短请求。它不会创建 rollout、broker 账户或订单，也不会写入正式决策历史；每个 worker 会创建一个不再恢复的原生临时 session，并把 session ID、CLI 版本、实际命令、耗时、退出码和完整输出写入独立日志。

先检查三组命令：

```bash
./run_concurrency_smoke --harness dsh --dry-run
./run_concurrency_smoke --harness claude --dry-run
./run_concurrency_smoke --harness codex --dry-run
```

确认后每次只运行一个供应商批次：

```bash
./run_concurrency_smoke --harness dsh
./run_concurrency_smoke --harness claude
./run_concurrency_smoke --harness codex
```

默认并发分别为 DSH 5、Claude Code 3、Codex 5，单 worker 超时 120 秒。Claude 默认三条均使用 `sonnet/high`；Codex 默认使用 GPT-5.6 Sol、GPT-5.6 Luna、GPT-6 Sol、GPT-6 Luna 和 GPT-6 Astra 五个正式模型配置并全部设为 `high`；DSH 的实际模型和推理档位由原生 profile 控制，脚本中的 `deepseek-flash/high` 只作为审计标签。可以用 `--count`、`--models`、`--reasoning-effort` 和 `--timeout` 覆盖默认值。

只有所有 worker 都以零状态退出、精确回复 `CONCURRENCY_OK` 且返回非空 session ID 时，批次才成功。结果写入 `parallel_runs/concurrency_<harness>_<timestamp>_<suffix>/summary.json`；该测试通过只证明 CLI/账户能承受目标并发，不替代完整 `run_rollout` 交易 smoke。

### 完整并发交易 smoke（实时模拟盘）

`run_parallel_rollouts` 会为一个供应商同时运行完整的 `run_rollout` 流程，包括独立账户、原生持久 session、联网研究、broker 操作、决策格式校验和日志。它只使用模拟资金，但会真实修改各 smoke rollout 的账户并可能提交限价方案。

先检查命令，不创建任何状态：

```bash
./run_parallel_rollouts --harness dsh --rollout-set live_smoke_dsh01 --dry-run
./run_parallel_rollouts --harness claude --rollout-set live_smoke_claude01 --dry-run
./run_parallel_rollouts --harness codex --rollout-set live_smoke_codex01 --dry-run
```

确认后按供应商依次运行，不要同时启动三组：

```bash
./run_parallel_rollouts --harness dsh --rollout-set live_smoke_dsh01
./run_parallel_rollouts --harness claude --rollout-set live_smoke_claude01
./run_parallel_rollouts --harness codex --rollout-set live_smoke_codex01
```

完整实时 smoke 不传 `--as-of`，可以在 08:00–20:00 美东时间内任意时刻启动，不要求正好位于正式决策窗口。broker 会把新方案的 `valid_from` 设为下一完整分钟，并把 `valid_until` 设为下一个 12:00、15:30、19:00 或 20:00 边界。第一轮主要验证研究、下单、session 和决策记录；边界过后使用同一个 rollout set 再运行一轮，才能继续验证 Yahoo 撮合与精确会话恢复。

默认 DSH 启动 5 条 `deepseek-flash` 标签轨迹，Claude Code 启动 `opus/sonnet/haiku` 三档，Codex 启动 GPT-5.6 Sol、GPT-5.6 Luna、GPT-6 Sol、GPT-6 Luna 和 GPT-6 Astra 五个正式模型配置，全部标记为 `high`。DSH 的实际模型和推理档位仍由原生 profile 决定。每个批次结果写入 `parallel_runs/full_<harness>_<timestamp>_<pid>/summary.json`，任一 rollout 失败时批次返回非零状态，但会等待并记录其他 rollout 的结果。

### Astra 五并发压力测试

`run_five_astra_high` 固定启动 5 条相互隔离的 `gpt-6-astra/high` 完整模拟交易 rollout，用于判断 Codex 在最重模型组合下能否稳定承受真实 5 并发。它复用 `run_parallel_rollouts` 的账户隔离、持久 session、超时、进程组清理、逐轨迹日志和批次汇总逻辑。2026-10-20 的恢复会话压力测试以 5/5 通过，正式 Codex 默认配置因此扩展为每波 5 并发。

必须使用专门的新 rollout set，并先 dry-run：

```bash
./run_five_astra_high --rollout-set astra_stress01 --dry-run
./run_five_astra_high --rollout-set astra_stress01
```

默认单条超时 900 秒并使用实时 broker 时间；历史 smoke 可显式传入带 UTC 偏移量的 `--as-of`。首次压力测试不要自动重试失败项：应先区分限流、排队、timeout、CLI 错误和单纯的决策格式错误。压力测试结果单独统计，不自动并入正式模型表现样本。

### 正式五波决策窗口

`run_decision_window` 用于 Codex、Claude Code 和 ZCode 的正式窗口执行。它固定运行 5 个顺序波次：Codex 每波并发 GPT-5.6 Sol、GPT-5.6 Luna、GPT-6 Sol、GPT-6 Luna 和 GPT-6 Astra 五档模型，Claude Code 每波并发三档模型，ZCode 每波只运行一条 `GLM-5.3` 审计标签轨迹；同一模型配置在每波只运行一条 rollout。当前波次全部成功、失败或超时并彻底停止后，才会装填下一波。单条失败不会跳过剩余波次，但窗口最终返回非零状态。ZCode 的实际模型由原生账户配置控制，`GLM-5.3` 只是与当前已核对配置一致的运行标签。

首次运行务必先 dry-run；`--window-index` 是从 1 开始、跨交易日连续递增的全局窗口序号，它决定五条 rollout 的轮换顺序：

```bash
./run_decision_window \
  --harness codex \
  --rollout-set official_codex \
  --window-index 1 \
  --dry-run

./run_decision_window \
  --harness claude \
  --rollout-set official_claude \
  --window-index 1 \
  --dry-run

./run_decision_window \
  --harness zcode \
  --rollout-set official_zcode \
  --window-index 1 \
  --dry-run
```

确认模型、rollout ID、波次顺序和命令后，去掉 `--dry-run` 才会启动完整窗口。正式实时运行不得传 `--as-of`；该参数只用于冻结时间的 smoke test。相同 `--rollout-set`、harness、模型列表和 rollout 编号会恢复原账户与精确原生 session，因此模型版本或实验规则变化时必须换用新的 rollout set。

窗口 1 的波次顺序是 `01, 02, 03, 04, 05`，窗口 2 是 `02, 03, 04, 05, 01`，依此循环。每波日志和汇总分别位于 `parallel_runs/window_<harness>_.../wave_<波次>_r<rollout>/`，窗口总汇总写入同一批次目录的 `summary.json`。按 Ctrl-C 会终止当前波次的全部子进程，且不会启动后续波次。

## 已有文件

- `BROKER.md`：模拟账户、限价单、延迟撮合、状态存储和 JSON 接口规范。
- `universe.txt`：冻结的可交易证券白名单。
- `templates/DECISION_FORMAT.md`：每轮最终决策记录的固定格式。
- `templates/DECISIONS.md`：每条轨迹的长期决策历史初始模板。
- `src/trading_broker/state_store.py` 与 `ledger.py`：原子账户快照、追加式审计流水和崩溃恢复。
- `src/trading_broker/market_data.py` 与 `market_cache.py`：单次批量 Yahoo 适配器和不可变共享缓存。
- `src/trading_broker/settlement.py`：确定性撮合后的现金、持仓、冻结和日内方向更新。
- `src/trading_broker/service.py`、`cli.py` 与 `./broker`：`status`、`settle`、`submit-plan`、`cancel` 接口。
- `src/trading_runner/` 与 `./run_rollout`：Codex、Claude Code、DSH、ZCode 原生 CLI 适配、持久会话、单轮编排、轨迹初始化、输出校验和完整运行日志。
- `./run_four_high`：保留的四模型手动测试工具；正式默认 Codex 配置已经扩展为每波 5 并发。
- `./run_concurrency_smoke`：对 Codex、Claude Code 或 DSH 做不交易的原生 CLI 并发连通性测试，并保存逐 worker 日志和批次汇总。
- `./run_parallel_rollouts`：按供应商并发执行完整的 broker-backed 实时模拟交易 rollout，并保存逐轨迹日志和批次汇总。
- `./run_five_astra_high`：固定执行 5 条 `gpt-6-astra/high` 完整 rollout 的真实五并发压力测试；该测试已于 2026-10-20 以 5/5 通过。
- `./run_decision_window`：对 Codex、Claude Code 或单并发 ZCode 执行正式的五波屏障调度、跨窗口 rollout 轮换和窗口级汇总。

## 尚未完成

1. 在 pilot 前固定 `yfinance` 版本，并验证白名单 ticker 映射、盘前盘后覆盖、公司行动字段和请求稳定性。
2. 在安装固定依赖的隔离环境中做 Yahoo 实际连通测试，并补齐公司行动、官方交易日历、失败重试和多进程压力测试。
3. 冻结 prompt、模型版本、harness 版本、订阅档位、并发上限和超时规则。
4. 在现有五波调度器之上实现四个决策窗口的定时唤醒，并加入防止同一窗口被意外重复执行的持久调度状态。
5. 确定收益、风险、最大回撤、换手、违规率、存活率和运行成本等评估指标。
6. 编写主方案/backup 选择、部分 backup 拒绝、撮合、资金冻结、日内方向限制、轨迹隔离和崩溃恢复测试。
7. 先用少量轨迹做一周 pilot，再决定是否扩展模型和重复数。
