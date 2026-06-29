# Universal RAG Evaluator

[中文](#中文说明) · [English](#english)

**Current release: v0.2.1**

A framework-agnostic, research-grade evaluation toolkit for Retrieval-Augmented Generation systems.

It accepts offline JSONL exports from **any RAG stack**—LlamaIndex, LangChain, Haystack, custom Python services, Java/Go backends, or production logs—and evaluates retrieval, answer quality, grounding, citations, abstention, temporal validity, robustness, latency, token usage, cost, and statistical significance.

> The evaluator does not require access to your model or vector database. Your RAG system only needs to export one row per query.

## Why this project

A single answer score cannot tell you why a RAG system failed. Universal RAG Evaluator separates the pipeline into measurable stages:

```text
Query → Retrieval → Context selection → Generation → Claims → Citations
          │                 │               │          │
       Recall/MRR      noise/time       completeness  support
```

It also supports the most useful diagnostic experiment for RAG:

- **Base**: answer without external context.
- **Oracle**: answer with gold evidence.
- **Retrieved**: answer with the system's real retrieval output.

This distinguishes generator limitations from retrieval failure and context harm.

---

# 中文说明

## 主要能力

| 评测层级 | 指标与功能 |
|---|---|
| 召回侧 | Hit@K、Recall@K、Precision@K、MRR、nDCG@K |
| 回答侧 | Claim Precision / Recall / F1、Exact Match、完整性 |
| 证据侧 | Faithfulness、Hallucination Rate、Citation Precision / Recall / F1 |
| 拒答 | 正确拒答、错误拒答、无证据强行回答 |
| 时间性 | Temporal Precision、Outdated Rate、Temporal Claim Accuracy |
| 鲁棒性 | 干扰文档比例、Base / Oracle / Retrieved 三条件诊断 |
| 工程指标 | 总延迟、分阶段延迟、P50/P95、Token、估算成本 |
| 实验统计 | Paired bootstrap 95% CI、sign-flip test、效应量、Holm 修正 |
| 分层分析 | 按领域、语言、难度、问题类型等 slices 自动汇总 |
| Judge 校准 | 模型 Judge 与人工标签的 Accuracy、F1、Cohen's κ |

## 1. 安装

需要 Python 3.10 或更高版本。

```bash
# 克隆项目后进入目录
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

检查 CLI：

```bash
rageval --help
```

## 2. 最快运行示例

```bash
rageval validate examples/gold.jsonl examples/run_a.jsonl --strict

rageval evaluate \
  examples/gold.jsonl \
  examples/run_a.jsonl \
  --ks 1,3,5,10 \
  --output results/run_a.json \
  --strict
```

一次评测会产生三个文件：

```text
results/run_a.json                 汇总指标、分层结果和复现 manifest
results/run_a.per_query.jsonl      每个问题的全部指标
results/run_a.md                   可直接阅读的 Markdown 报告
```

## 3. 接入任意 RAG 系统

评测器读取两个 UTF-8 JSONL 文件，通过 `query_id` 对齐。

### Gold benchmark

每行是一道问题：

```json
{
  "query_id": "q-001",
  "question": "谁创立了示例公司？",
  "answerable": true,
  "gold_doc_ids": ["doc-17"],
  "required_claims": ["Alice 创立了示例公司"],
  "reference_answer": "Alice 创立了示例公司。",
  "as_of": "2026-06-01",
  "slices": {
    "domain": "company_history",
    "language": "zh",
    "difficulty": "easy"
  }
}
```

### System run

每行是 RAG 系统对同一问题的一次完整运行：

```json
{
  "query_id": "q-001",
  "answer": "Alice 创立了示例公司。[1]",
  "retrieved": [
    {
      "doc_id": "doc-17",
      "rank": 1,
      "score": 0.91,
      "text": "Alice founded ExampleCo in 2019.",
      "temporally_valid": true,
      "outdated": false,
      "distractor": false
    }
  ],
  "predicted_claims": [
    {
      "text": "Alice 创立了示例公司",
      "supported": true,
      "relevant": true,
      "temporal_correct": true
    }
  ],
  "citations": [
    {
      "claim": "Alice 创立了示例公司",
      "doc_ids": ["doc-17"],
      "supported": true
    }
  ],
  "abstained": false,
  "latency_ms": 420,
  "stage_latency_ms": {
    "retrieval": 38,
    "rerank": 52,
    "generation": 330
  },
  "prompt_tokens": 550,
  "completion_tokens": 38,
  "estimated_cost_usd": 0.0021
}
```

完整字段说明见 [`docs/data-contract.md`](docs/data-contract.md)。近两年论文方法与本项目功能的对应关系见 [`docs/research-methods.md`](docs/research-methods.md)。

### 最低接入要求

你的系统最少只需导出：

```json
{"query_id":"q-001","answer":"...","retrieved":[{"doc_id":"doc-17","rank":1}]}
```

只有 `query_id`、`answer` 和 `retrieved` 是 run 的基础字段。Claim、引用、时间和成本字段可以逐步补充。评测器只计算有可用标签的指标，不会强制调用 LLM Judge。

## 4. 比较两个 RAG 系统

先分别评测：

```bash
rageval evaluate examples/gold.jsonl examples/run_a.jsonl --output results/a.json
rageval evaluate examples/gold.jsonl examples/run_b.jsonl --output results/b.json
```

再进行逐问题配对比较：

```bash
rageval compare \
  results/a.per_query.jsonl \
  results/b.per_query.jsonl \
  --metrics answer_claim_f1,recall@5,citation_f1,latency_ms \
  --iterations 10000 \
  --output results/a_vs_b.json
```

输出包括：

- 每个指标实际使用的配对问题数和因缺失标签排除的问题数；
- 两个系统的均值；
- `B - A` 的平均差值；
- paired bootstrap 95% 置信区间；
- exact / Monte Carlo sign-flip p 值；
- paired effect size（Cohen's dz）；
- 多指标比较的 Holm 校正 p 值。

同一 benchmark 上比较系统时，应使用配对检验，而不是把两组问题当成互不相关样本。

## 5. 定位问题来自召回还是回答

准备三份已经评测后的 per-query 文件：

```text
base.per_query.jsonl        不给模型上下文
oracle.per_query.jsonl      只给模型 gold evidence
retrieved.per_query.jsonl   给模型真实检索结果
```

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

诊断标签：

| 标签 | 含义 |
|---|---|
| `generator_or_task_failure` | 即使使用 Oracle 证据也回答不好 |
| `retrieval_or_context_failure` | Oracle 能回答，但真实检索上下文下失败 |
| `context_harm` | 加入真实上下文后比无上下文更差 |
| `pass` | 当前指标达到要求 |

## 6. 校准 LLM Judge

不要在未经验证时把 LLM Judge 的分数当作真值。先准备人工和 Judge 的二元标签：

```json
{"query_id":"q1","claim_id":"c1","human_label":true,"judge_label":true}
{"query_id":"q2","claim_id":"c1","human_label":false,"judge_label":true}
```

运行：

```bash
rageval calibrate examples/judge_labels.jsonl --output results/judge_calibration.json
```

建议至少报告 Accuracy、Precision、Recall、F1 和 Cohen's κ，并人工检查 Judge 的假阳性与假阴性。

## 7. 推荐实验流程

```text
1. 冻结 benchmark 和 corpus
2. 给 query、document、claim 分配稳定 ID
3. 先运行 validate，不调用任何付费模型
4. 先做 retrieval-only baseline
5. 再固定检索结果比较 generator/prompt
6. 运行 Base / Oracle / Retrieved 三条件
7. 按 domain、language、difficulty、temporal_type 分层
8. 输出 per-query 结果和失败案例
9. 用配对置信区间和配对显著性检验比较
10. 记录哈希、Git commit、随机种子、模型版本、Token 和成本
```

一次消融实验原则上只改变一个因素，例如：

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

## 8. Codex Skill

仓库自带项目级 Skill：

```text
.agents/skills/universal-rag-evaluator/SKILL.md
```

在 Codex 中可以直接输入：

```text
使用 $universal-rag-evaluator 检查当前项目的 RAG 评测方案。
先识别现有 benchmark、检索输出、回答输出和缓存，再给出最低成本的实验矩阵。
在调用付费模型前先验证数据，并估算模型调用次数和 Token 上限。
```

Skill 会要求实验固定变量、复用缓存、分别评测召回与回答、校准 Judge，并输出可复现 manifest。

## 9. 项目结构

```text
universal-rag-evaluator/
├── .agents/skills/             Codex 评测 Skill
├── .github/workflows/ci.yml    Python 3.10–3.13 CI
├── docs/                       数据协议、实验方法与论文方法映射
├── examples/                   可直接运行的示例
├── src/rageval_lab/            核心库和 CLI
├── tests/                      单元测试
├── README.md
├── pyproject.toml
└── LICENSE
```

## 10. 当前边界

- 本项目默认使用**确定性离线标签**，不会私自调用外部模型。
- Claim 的语义等价、faithfulness 和 citation support 需要由人工或外部 Judge/规则适配器写入 run JSONL。
- 当前检索指标使用文档级 relevance；passage/claim 级 evidence 可以通过更细粒度 `doc_id` 或扩展适配器表达。
- 生产日志中含有隐私或商业数据时，应先脱敏再导出。

---

# English

## Quick start

```bash
python -m pip install -e .
rageval validate examples/gold.jsonl examples/run_a.jsonl --strict
rageval evaluate examples/gold.jsonl examples/run_a.jsonl --output results/run_a.json
```

## Core commands

```bash
# Evaluate one run
rageval evaluate GOLD.jsonl RUN.jsonl --ks 1,3,5,10 --output results/run.json

# Paired comparison of two evaluated runs
rageval compare A.per_query.jsonl B.per_query.jsonl \
  --metrics answer_claim_f1,recall@5,citation_f1

# Diagnose Base / Oracle / Retrieved conditions
rageval diagnose BASE.per_query.jsonl ORACLE.per_query.jsonl RETRIEVED.per_query.jsonl \
  --metric answer_claim_f1

# Calibrate a binary model judge against human labels
rageval calibrate JUDGE_LABELS.jsonl
```

## Principles

1. Evaluate retrieval and generation separately.
2. Keep the benchmark and query set fixed.
3. Change one experimental factor at a time.
4. Save per-query outputs, not only averages.
5. Use paired statistics for shared queries.
6. Calibrate model judges against human annotations.
7. Report latency, tokens and cost together with quality.

See [`docs/methodology.md`](docs/methodology.md), [`docs/data-contract.md`](docs/data-contract.md), and [`docs/research-methods.md`](docs/research-methods.md) for details.

## License

MIT
