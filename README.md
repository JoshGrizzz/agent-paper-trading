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
- **Market:** Agents may trade U.S. stocks and ETFs from the same fixed list of tickers.
- **Autonomy:** No research process or trading strategy is prescribed. Agents have access to the web, tools, and coding capabilities, but they are never required to use them. This minimizes behavioral steering and allows us to observe the "natural" behavior of each model in its agent harness.
- **Orders:** Market orders are disabled. Agents submit limit order plans with one primary candidate and up to two optional backups.
- **Execution:** A shared broker simulator settles orders using Yahoo Finance market data and the same matching rules for every rollout.
- **Constraints:** No borrowing, short selling, or same day round trips. Inverse ETFs are allowed.
- **Memory:** Every rollout maintains its own persistent conversation, decision log, account, and order history.
- **Isolation:** Agents cannot inspect other rollouts or copy decisions from other competitors.
- **Human role:** Humans operate the schedule and infrastructure but do not make trading decisions for the agents.
