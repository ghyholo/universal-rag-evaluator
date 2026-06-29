---
name: universal-rag-evaluator
description: Design, validate, execute, diagnose, and report framework-agnostic RAG evaluations covering retrieval, answers, grounding, citations, abstention, temporal correctness, robustness, cost, judge calibration, and paired statistics.
---

# Universal RAG Evaluator Skill

Use this skill when evaluating any RAG system, designing an experiment, comparing variants, or investigating quality regressions.

## Required workflow

1. Inspect the corpus, benchmark, pipeline stages, output schema, and existing caches.
2. Convert outputs to the repository JSONL contract in `docs/data-contract.md`.
3. Run strict validation before any paid model call.
4. Establish retrieval-only baselines before answer-side experiments.
5. Run Base, Oracle, and Retrieved context conditions when diagnosing the pipeline.
6. Evaluate retrieval, answer claims, grounding, citations, abstention, temporal correctness, latency, tokens, and cost separately.
7. Compare systems query-by-query with paired confidence intervals, sign-flip tests, effect sizes, and Holm correction for multiple metrics.
8. Report slice-level failures and representative examples, not only aggregate scores.
9. Calibrate model judges against human labels before using them at scale.
10. Save a reproducibility manifest and all per-query outputs.

## Guardrails

- Never change more than one experimental factor without labeling the run as a compound change.
- Reuse retrieval, context, answer, and judge caches using content hashes.
- Record corpus hash, benchmark hash, configuration, model version, prompt version, seed, and commit SHA.
- Do not infer semantic claim equivalence with raw string matching; export human/rule/judge labels explicitly.
- Do not claim an improvement from an unpaired test when systems share queries.
- Do not rerun paid generation if cached outputs already match the experiment fingerprint.
- Estimate the number of model calls and token budget before execution.

## Standard commands

```bash
rageval validate GOLD.jsonl RUN.jsonl --strict
rageval evaluate GOLD.jsonl RUN.jsonl --ks 1,3,5,10 --output results/run.json
rageval compare results/a.per_query.jsonl results/b.per_query.jsonl \
  --metrics answer_claim_f1,recall@5,citation_f1
rageval diagnose results/base.per_query.jsonl results/oracle.per_query.jsonl \
  results/retrieved.per_query.jsonl --metric answer_claim_f1
rageval calibrate judge_labels.jsonl
```

Read `references/experiment-checklist.md` before starting a final experiment.
