# Agent Paper Trading

## Description

Without a doubt, top tier LLMs are powerful, and coding agents are remarkably good at executing instructions. But how do they behave in an environment that is noisy, nonstationary, and continuously evolving?

Motivated purely by curiosity (we are not writing a paper here, haha), we turned to financial markets. This project is inspired by [LiveTradeBench](https://arxiv.org/abs/2511.03628) and [AI-Trader](https://arxiv.org/abs/2512.10971).

We push this idea one step further by letting coding agents trade (almost) autonomously. We only tell them that they are participating in a paper trading competition, provide a small set of rules and a fixed list of tradable tickers, and leave the trading decisions entirely to them.

## Agents

| Harness | Models | Rollouts per model | Total |
| --- | --- | ---: | ---: |
| Codex | GPT-5.6 Sol, GPT-5.6 Luna, GPT-6 Sol, GPT-6 Luna, GPT-6 Astra | 5 | 25 |
| Claude Code | Opus, Sonnet, Haiku | 5 | 15 |
| DSH | DeepSeek Flash | 5 | 5 |
| ZCode | GLM-5.3 | 5 | 5 |
| **Total** | **10 model configurations** |  | **50** |

## Protocol

- **Objective:** Maximize the final value of an isolated paper trading account.
- **Initial capital:** Each rollout starts with USD 100,000 in cash and no positions.
- **Schedule:** Agents wake at 08:30, 12:00, 15:30, and 19:00 ET on each U.S. trading day.
- **Competition end:** All active cohorts receive the same fixed end timestamp: 2026-12-02 16:00 ET.
- **Market:** Agents may trade U.S. stocks and ETFs from the same fixed list of tickers.
- **Autonomy:** No research process or trading strategy is prescribed. Agents have access to the web, tools, and coding capabilities, but they are never required to use them. This minimizes behavioral steering and allows us to observe the "natural" behavior of each model in its agent harness.
- **Orders:** Market orders are disabled. Agents submit limit order plans with one primary candidate and up to two optional backups.
- **Execution:** A shared broker simulator settles orders using Yahoo Finance market data and the same matching rules for every rollout.
- **Constraints:** No borrowing, short selling, or same day round trips. Inverse ETFs are allowed.
- **Memory:** Every rollout maintains its own persistent conversation, decision log, account, and order history.
- **Isolation:** Agents cannot inspect other rollouts or copy decisions from other competitors.
- **Human role:** Humans operate the schedule and infrastructure but do not make trading decisions for the agents.

## Claude V2 protocol

The original 15 Claude Code rollouts remain an archived first-generation cohort under the USD 100,000 protocol above. Claude V2 is a clean successor cohort with one new rollout for each original rollout.

- **Handoff:** All predecessors are settled and valued at one shared ET timestamp. Each successor starts with cash exactly equal to its predecessor's final equity.
- **Clean restart:** Successors inherit no positions, orders, conversation, session, or decision history.
- **Lineage:** A cohort manifest records the predecessor, handoff timestamp, exact transferred equity, and state checksum. This manifest is not exposed to the Agent.
- **Workspace isolation:** Each V2 Agent runs inside its own `workspace/`; broker state, runner state, lineage data, project source, and other rollouts remain outside that workspace.
- **Optional Python capability:** V2 Claude Code may invoke an audited `python` or `python3` launcher. Code runs in a namespace and chroot with a disposable Conda overlay, strict resource limits, an empty host environment, and access only to its own writable `research/` directory plus read-only copies of its universe and decision history. Public internet access remains available.
- **No behavioral steering:** V2 receives the same trading instructions and fixed end timestamp as the other active cohorts. The prompt does not advertise or recommend Python, research, or any strategy. The capability is available without directing the Agent to use it.

The handoff is preview-only unless `--execute` is supplied:

```bash
./prepare_claude_successors \
  --source-set official_claude \
  --target-set official_claude_v2

./prepare_claude_successors \
  --source-set official_claude \
  --target-set official_claude_v2 \
  --execute
```

After handoff, the successor cohort uses the existing decision-window entry point with `--rollout-set official_claude_v2`.
