# Evaluation methodology

## 1. Separate stages

Report retrieval, answer, grounding/citation, abstention, temporal correctness, robustness, and operational cost separately. Avoid collapsing them into one score before diagnosing failures.

## 2. Minimum experiment matrix

Hold corpus, benchmark, generator, prompt, top-K, and context-token budget constant while changing one component at a time.

Retrieval ablations:

- sparse vs dense vs hybrid;
- fusion strategy;
- query expansion / HyDE;
- reranker;
- chunk size and overlap;
- top-K and context budget;
- metadata or temporal filters.

Answer ablations:

- Base, Oracle, Retrieved context;
- citation requirement;
- abstention threshold;
- generator and prompt variants;
- context ordering and compression.

## 3. Reporting requirements

Always preserve per-query outputs and report:

- macro means;
- slice-level results;
- failure examples;
- latency/token/cost;
- paired confidence intervals;
- paired significance tests and effect sizes;
- exact model and prompt versions;
- benchmark/corpus hashes and Git commit.

## 4. Human and model judges

Before using a model judge at scale:

1. Define an atomic claim-level rubric.
2. Double-annotate a representative subset.
3. Resolve disagreements and freeze the guideline.
4. Compare judge labels with human labels.
5. Inspect false positives and false negatives.
6. Freeze judge model, temperature, prompt and parser.
7. Cache judge outputs by content hash.

## 5. Statistical comparison

Use paired tests when systems answer the same queries. Report the paired mean difference, bootstrap confidence interval, sign-flip p-value, and paired effect size. Correct p-values when testing many metrics or variants.

## 6. Cost control

Validate all JSONL files before paid calls. Cache four layers independently:

1. retrieval output;
2. assembled context;
3. generated answer;
4. judge decision.

Use a small development set for pipeline debugging, then freeze the pipeline before running the final benchmark.
