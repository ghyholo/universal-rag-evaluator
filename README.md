<div align="center">

<h1>Universal RAG Evaluator</h1>

<p><strong>别只问“RAG 得了多少分”，更要知道它为什么答错。</strong></p>

<p>
一个面向研究与工程实践的通用 RAG 评测工具箱。<br />
不绑定框架，不要求连接你的模型或向量数据库，只需要导出 JSONL 即可开始评测。
</p>

[![CI](https://github.com/ghyholo/universal-rag-evaluator/actions/workflows/ci.yml/badge.svg)](https://github.com/ghyholo/universal-rag-evaluator/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.1-orange)](CHANGELOG.md)

[中文说明](#中文说明) · [English](#english)

</div>

---

# 中文说明

## 它解决什么问题？

一个 RAG 系统回答错了，原因可能完全不同：

- 检索阶段根本没有找到正确证据；
- 找到了证据，但上下文里混入了大量噪声或过期内容；
- 模型看到了证据，却没有正确使用；
- 答案看起来合理，但实际上没有证据支持；
- 系统应该拒答，却仍然给出了一个“像真的”答案。

只看一个最终答案分数，很难判断问题到底出在哪里。

**Universal RAG Evaluator 会把 RAG 流程拆开评测：**

```text
问题
  ↓
检索 ──→ 上下文选择 ──→ 生成答案 ──→ Claim ──→ 引用
  │           │              │           │         │
Recall/MRR   噪声/时间性    完整性      忠实性    证据支持
```

它适合：

- 正在做 RAG 论文实验，需要可复现评测流程的人；
- 想比较 BM25、Dense、Hybrid、Reranker、HyDE 等方案的人；
- 想知道问题出在召回侧还是回答侧的开发者；
- 需要同时关注质量、延迟、Token 和成本的工程团队。

---

## 你可以评测什么？

| 评测维度 | 主要内容 |
|---|---|
| 🔎 检索质量 | Hit@K、Recall@K、Precision@K、MRR、nDCG@K |
| ✍️ 回答质量 | Claim Precision / Recall / F1、Exact Match、完整性 |
| 🧾 证据与引用 | Faithfulness、Hallucination Rate、Citation Precision / Recall / F1 |
| 🙅 拒答能力 | 正确拒答、错误拒答、无证据强行回答 |
| 🕒 时间正确性 | Temporal Precision、Outdated Rate、Temporal Claim Accuracy |
| 🧪 鲁棒性 | 干扰文档比例、Base / Oracle / Retrieved 三条件诊断 |
| ⚙️ 工程表现 | 总延迟、分阶段延迟、P50/P95、Token、估算成本 |
| 📊 实验统计 | Paired bootstrap、sign-flip test、Cohen's dz、Holm 修正 |
| 🧩 分层分析 | 按领域、语言、难度、问题类型等 slice 自动汇总 |
| 🤖 Judge 校准 | Accuracy、Precision、Recall、F1、Cohen's κ |

> 核心评测器不会自动调用外部 LLM。你可以先完成完全离线、可复现的评测，再按需要接入人工标签或经过校准的 Model Judge。

---

## 3 分钟快速开始

### 1. 克隆并安装

```bash
git clone https://github.com/ghyholo/universal-rag-evaluator.git
cd universal-rag-evaluator

python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

检查是否安装成功：

```bash
rageval --help
```

### 2. 运行内置示例

```bash
rageval validate examples/gold.jsonl examples/run_a.jsonl --strict

rageval evaluate \
  examples/gold.jsonl \
  examples/run_a.jsonl \
  --ks 1,3,5,10 \
  --output results/run_a.json \
  --strict
```

### 3. 查看结果

一次评测会生成三类文件：

```text
results/run_a.json                 汇总指标、分层结果和复现信息
results/run_a.per_query.jsonl      每个问题的详细指标
results/run_a.md                   适合直接阅读的 Markdown 报告
```

这样既能看总体结果，也能继续定位具体失败样本。

---

## 如何接入自己的 RAG 系统？

你不需要修改现有 RAG 架构，也不需要让评测器连接你的数据库。

只要准备两个 JSONL 文件：

### Gold benchmark

每一行描述一道问题及其正确证据：

```json
{"query_id":"q-001","question":"谁创立了示例公司？","answerable":true,"gold_doc_ids":["doc-17"],"required_claims":["Alice 创立了示例公司"]}
```

### System run

每一行保存系统实际输出：

```json
{"query_id":"q-001","answer":"Alice 创立了示例公司。[1]","retrieved":[{"doc_id":"doc-17","rank":1}]}
```

最基础的接入只需要：

- `query_id`
- `answer`
- `retrieved`

之后可以逐步补充 Claim、引用、时间标签、延迟、Token 和成本，不需要一开始就准备所有字段。

更完整的字段说明：

- [数据协议](docs/data-contract.md)
- [接入适配器示例](docs/adapters.md)

---

## 四个最常用的工作流

### 1. 评测一个系统

```bash
rageval evaluate \
  benchmark.jsonl \
  system_run.jsonl \
  --ks 1,3,5,10 \
  --output results/system.json \
  --strict
```

适用于：查看一个系统当前的召回、回答、引用、拒答和成本表现。

### 2. 比较两个系统

```bash
rageval evaluate benchmark.jsonl run_a.jsonl --output results/a.json
rageval evaluate benchmark.jsonl run_b.jsonl --output results/b.json

rageval compare \
  results/a.per_query.jsonl \
  results/b.per_query.jsonl \
  --metrics answer_claim_f1,recall@5,citation_f1,latency_ms \
  --iterations 10000 \
  --output results/a_vs_b.json
```

输出会包含：

- 两个系统的平均结果；
- `B - A` 的逐问题平均差值；
- paired bootstrap 95% 置信区间；
- exact / Monte Carlo sign-flip p 值；
- Cohen's dz 效应量；
- Holm 多重比较修正；
- 每个指标实际使用和排除的配对样本数。

### 3. 判断问题出在召回还是回答

准备三个条件：

| 条件 | 输入给模型的内容 | 用途 |
|---|---|---|
| Base | 不提供外部上下文 | 测试模型自身能力 |
| Oracle | 只提供 Gold evidence | 测试理想证据下的生成能力 |
| Retrieved | 提供系统真实检索结果 | 测试完整 RAG 流程 |

运行：

```bash
rageval diagnose \
  results/base.per_query.jsonl \
  results/oracle.per_query.jsonl \
  results/retrieved.per_query.jsonl \
  --metric answer_claim_f1 \
  --pass-threshold 0.8 \
  --output results/context_diagnosis.json
```

系统会把问题标记为：

- `generator_or_task_failure`
- `retrieval_or_context_failure`
- `context_harm`
- `pass`

### 4. 校准 LLM Judge

先准备一小部分人工标签：

```json
{"query_id":"q1","claim_id":"c1","human_label":true,"judge_label":true}
{"query_id":"q2","claim_id":"c1","human_label":false,"judge_label":true}
```

再运行：

```bash
rageval calibrate \
  examples/judge_labels.jsonl \
  --output results/judge_calibration.json
```

不要在未经验证时直接把 Model Judge 当作真值。建议先检查 Accuracy、F1、Cohen's κ，以及 Judge 的假阳性和假阴性案例。

---

## 一套更稳妥的实验流程

```text
1. 冻结 benchmark 和 corpus
2. 给 query、document、claim 分配稳定 ID
3. 先运行严格校验，不调用付费模型
4. 先做 retrieval-only baseline
5. 固定检索结果后，再比较 generator 或 prompt
6. 运行 Base / Oracle / Retrieved 三条件
7. 按领域、语言、难度和时间类型分层
8. 保存 per-query 结果和失败案例
9. 使用逐问题配对统计检验
10. 记录哈希、Git commit、模型版本、Token、延迟和成本
```

一次消融实验最好只改变一个因素，例如：

- sparse / dense / hybrid；
- fusion 方法；
- embedding 模型；
- reranker；
- chunk size / overlap；
- top-K；
- context token budget；
- query expansion / HyDE；
- generator 或 prompt；
- citation / abstention 策略。

详细方法见：[评测方法指南](docs/methodology.md)。

---

## Codex Skill

仓库内置了项目级 Codex Skill：

```text
.agents/skills/universal-rag-evaluator/SKILL.md
```

在 Codex 中可以直接输入：

```text
使用 $universal-rag-evaluator 检查当前项目的 RAG 评测方案。
先识别 benchmark、检索输出、回答输出和缓存，再给出最低成本的实验矩阵。
在调用付费模型前先验证数据，并估算模型调用次数和 Token 上限。
```

Skill 会帮助你：

- 检查数据是否满足评测要求；
- 拆分召回侧和回答侧实验；
- 规划 Base / Oracle / Retrieved 三条件；
- 复用 retrieval、context、answer 和 judge 缓存；
- 生成可复现的实验记录与报告。

---

## 文档导航

| 文档 | 适合什么时候看 |
|---|---|
| [Data contract](docs/data-contract.md) | 准备 benchmark 和 system run 时 |
| [Adapter guide](docs/adapters.md) | 把现有 RAG 输出转换为 JSONL 时 |
| [Evaluation methodology](docs/methodology.md) | 设计消融实验和统计方法时 |
| [Research methods](docs/research-methods.md) | 查看近两年论文方法如何映射到项目功能时 |
| [Changelog](CHANGELOG.md) | 查看版本变化时 |
| [Contributing](CONTRIBUTING.md) | 参与开发或新增指标时 |

---

## 项目结构

```text
universal-rag-evaluator/
├── .agents/skills/             Codex 评测 Skill
├── .github/workflows/ci.yml    自动化测试
├── docs/                       数据协议与实验方法
├── examples/                   可直接运行的示例
├── src/rageval_lab/            核心库和 CLI
├── tests/                      单元测试
├── README.md
├── pyproject.toml
└── LICENSE
```

---

## 当前边界

为了让核心结果保持可复现，项目目前坚持以下原则：

- 默认使用确定性离线标签，不会私自调用外部模型；
- Claim 语义等价、faithfulness 和 citation support 需要由人工、规则或外部 Judge 提供；
- 当前检索指标以文档级 relevance 为主；更细粒度评测可以使用 passage/claim 级 ID；
- 生产日志含有隐私或商业数据时，应先脱敏再导出。

这些边界不是限制项目扩展，而是为了避免评测工具在用户不知情的情况下引入额外模型、费用或不可复现因素。

---

# English

## What is Universal RAG Evaluator?

Universal RAG Evaluator is a framework-agnostic toolkit for diagnosing and comparing RAG systems.

Instead of reducing the whole pipeline to one answer score, it evaluates:

- retrieval quality;
- answer claims and completeness;
- grounding and citations;
- abstention behavior;
- temporal correctness and distractors;
- latency, tokens and estimated cost;
- paired statistical significance;
- agreement between human labels and model judges.

It works with any RAG stack that can export one JSONL row per query. No direct model or vector-database access is required.

## Quick start

```bash
git clone https://github.com/ghyholo/universal-rag-evaluator.git
cd universal-rag-evaluator
python -m pip install -e .

rageval validate examples/gold.jsonl examples/run_a.jsonl --strict
rageval evaluate examples/gold.jsonl examples/run_a.jsonl --output results/run_a.json
```

## Core commands

```bash
# Evaluate one run
rageval evaluate GOLD.jsonl RUN.jsonl \
  --ks 1,3,5,10 \
  --output results/run.json

# Compare two evaluated runs
rageval compare A.per_query.jsonl B.per_query.jsonl \
  --metrics answer_claim_f1,recall@5,citation_f1

# Diagnose Base / Oracle / Retrieved conditions
rageval diagnose BASE.per_query.jsonl ORACLE.per_query.jsonl RETRIEVED.per_query.jsonl \
  --metric answer_claim_f1

# Calibrate a binary model judge
rageval calibrate JUDGE_LABELS.jsonl
```

## Evaluation principles

1. Evaluate retrieval and generation separately.
2. Keep the benchmark and query set fixed.
3. Change one experimental factor at a time.
4. Preserve per-query outputs, not only averages.
5. Use paired statistics when systems share queries.
6. Calibrate model judges against human annotations.
7. Report latency, tokens and cost together with quality.

For complete documentation, see:

- [Data contract](docs/data-contract.md)
- [Adapter guide](docs/adapters.md)
- [Evaluation methodology](docs/methodology.md)
- [Research method mapping](docs/research-methods.md)

## License

MIT
