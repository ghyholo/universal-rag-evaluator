# Data contract

Universal RAG Evaluator joins two UTF-8 JSONL files by `query_id`.

## Gold benchmark row

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `query_id` | string | yes | Stable unique identifier |
| `question` | string | yes | User query |
| `answerable` | boolean | yes | Whether the corpus contains sufficient evidence |
| `gold_doc_ids` | string[] | recommended | Relevant evidence identifiers |
| `required_claims` | string[] or object[] | recommended | Atomic claims expected in a complete answer |
| `reference_answer` | string | optional | Exact-match reference |
| `as_of` | string | optional | Evaluation cutoff date |
| `slices` | object | optional | Domain/language/difficulty/temporal type, etc. |

A required claim object may contain extra metadata, but must have `text`.

## System run row

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `query_id` | string | yes | Matches the benchmark row |
| `answer` | string | yes | Generated answer; use an empty string for abstention |
| `retrieved` | object[] | yes | Ranked retrieved evidence |
| `predicted_claims` | string[] or object[] | optional | Claims extracted from the answer |
| `citations` | object[] | optional | Claim-to-document mappings |
| `abstained` | boolean | optional | Explicit abstention flag |
| `latency_ms` | number | optional | End-to-end latency |
| `stage_latency_ms` | object | optional | Retrieval/rerank/generation latency |
| `prompt_tokens` | number | optional | Prompt tokens |
| `completion_tokens` | number | optional | Completion tokens |
| `estimated_cost_usd` | number | optional | Estimated request cost |

## Retrieved object

`doc_id` is required. Recommended fields are `rank`, `score`, `text`, `timestamp`, `temporally_valid`, `outdated`, `distractor`, and arbitrary `metadata`.

## Predicted claim object

```json
{
  "text": "atomic claim",
  "supported": true,
  "relevant": true,
  "temporal_correct": true
}
```

The three Boolean labels may come from a human review, deterministic rule, or calibrated model judge. The evaluator never fabricates them.

## Citation object

```json
{
  "claim": "atomic claim",
  "doc_ids": ["document-id"],
  "supported": true
}
```

When `supported` is absent, the evaluator falls back to overlap with `gold_doc_ids`. Explicit claim-level support labels are preferred because document relevance alone does not guarantee citation entailment.

## Judge calibration row

```json
{"query_id":"q1","claim_id":"c1","human_label":true,"judge_label":true}
```
