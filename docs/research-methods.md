# Research basis and method mapping

This project translates recent RAG evaluation research into reusable experiment rules. It does not redistribute paper text or datasets; links point to the original paper pages.

| Work | Experiment idea used by this project | Project implementation |
|---|---|---|
| [ARES (NAACL 2024)](https://arxiv.org/abs/2311.09476) | Separate context relevance, answer faithfulness, and answer relevance; calibrate automated judges with a human-labeled set | Separate metric families and `rageval calibrate` |
| [CRAG (2024)](https://arxiv.org/abs/2406.04744) | Test dynamic facts, long-tail entities, complex questions, and hallucination under changing evidence | temporal fields, answerability/abstention, slice dimensions |
| [RAGBench / TRACe (2024)](https://arxiv.org/abs/2407.11005) | Use explainable, actionable labels instead of a single opaque score | context/answer/grounding/completeness metrics kept separate |
| [BRIGHT (2024)](https://arxiv.org/abs/2407.12883) | Include reasoning-intensive retrieval where lexical or shallow semantic matching is insufficient | difficulty and reasoning-type slices; retrieval-only baselines |
| [Face4RAG (2024)](https://arxiv.org/abs/2407.01080) | Evaluate factual-consistency error types rather than only overall answer correctness | claim-level support labels and hallucination rate |
| [RAGChecker (2024)](https://arxiv.org/abs/2408.08067) | Diagnose retrieval and generation with fine-grained claim-level metrics | claim precision/recall/F1, grounding and citation metrics |
| [MIRAGE-Bench (2024)](https://arxiv.org/abs/2410.13716) | Multilingual evaluation and judge/heuristic combination | language slices and external calibrated judge contract |
| [MTRAG (2025)](https://arxiv.org/abs/2501.03468) | Multi-turn, non-standalone, unanswerable and cross-domain queries | arbitrary slices, stable query IDs, abstention metrics |
| [mmRAG (2025)](https://arxiv.org/abs/2505.11180) | Modular evaluation across text, tables and knowledge graphs | framework-neutral document IDs and modality metadata |
| [GaRAGe (2025)](https://arxiv.org/abs/2506.07671) | Grounding-passage annotations, relevance-aware factuality, source attribution and deflection | explicit claim support, citation support and abstention metrics |
| [ChronoQA (2025)](https://arxiv.org/abs/2508.12282) | Absolute, relative, aggregate, explicit and implicit temporal question categories | temporal validity metrics and temporal-type slices |
| [MM-BRIGHT (2026)](https://arxiv.org/abs/2601.09562) | Reasoning-intensive multimodal retrieval | schema permits modality metadata; future multimodal adapters |

## Experimental rules derived from the literature

1. **Do not use only an end-to-end answer score.** Measure retrieval, context quality, generation, grounding, citations and abstention independently.
2. **Use atomic claims.** Long-form answer scoring should operate at claim level so missing, unsupported and irrelevant statements remain distinguishable.
3. **Run Base, Oracle and Retrieved conditions.** This separates generator capability from retrieval/context failure.
4. **Include unanswerable and adversarial queries.** Measure correct deflection and unsafe answering rather than rewarding plausible guessing.
5. **Stratify the benchmark.** Report domain, language, difficulty, popularity, temporal type, multi-hop and modality slices.
6. **Calibrate model judges.** Compare model labels with human labels and report agreement before scaling the judge.
7. **Use paired statistics.** Systems evaluated on the same queries must be compared query-by-query, with confidence intervals and effect sizes.
8. **Record cost and latency.** Quality improvements should be interpreted together with token, latency and monetary cost changes.
9. **Preserve per-query artifacts.** Aggregate scores alone are insufficient for error analysis or reproducibility.
10. **Change one factor per ablation.** Compound changes must be explicitly labeled and should not be used to attribute causality to one component.
