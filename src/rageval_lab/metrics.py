from __future__ import annotations

import math
import re
from collections.abc import Iterable
from statistics import mean
from typing import Any


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def normalize_text(text: str) -> str:
    """Conservative language-agnostic normalization for exact offline labels."""
    return re.sub(r"\s+", "", text).casefold().strip()


def _claim_text(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("text", ""))
    return str(claim)


def _claim_set(claims: Iterable[Any]) -> set[str]:
    return {normalize_text(_claim_text(c)) for c in claims if _claim_text(c).strip()}


def _set_prf(predicted: set[str], gold: set[str]) -> tuple[float, float, float]:
    overlap = len(predicted & gold)
    precision = safe_div(overlap, len(predicted))
    recall = safe_div(overlap, len(gold))
    f1 = safe_div(2 * precision * recall, precision + recall)
    return precision, recall, f1


def retrieval_metrics(
    gold_doc_ids: list[str], retrieved: list[dict[str, Any]], ks: Iterable[int]
) -> dict[str, float]:
    """Compute binary retrieval metrics and optional temporal/noise metrics."""
    gold = set(map(str, gold_doc_ids))
    ranked = [str(item.get("doc_id", "")) for item in retrieved]
    result: dict[str, float] = {"retrieved_count": float(len(ranked))}
    if not gold:
        result["retrieval_abstention"] = float(len(ranked) == 0)
        result["retrieval_overreach"] = float(len(ranked) > 0)
        return result

    first_relevant_rank = next(
        (i + 1 for i, doc_id in enumerate(ranked) if doc_id in gold), None
    )
    result["mrr"] = 1.0 / first_relevant_rank if first_relevant_rank else 0.0

    for k in ks:
        top_items = retrieved[:k]
        top_ids = ranked[:k]
        unique_hits = len(set(top_ids) & gold)
        result[f"hit@{k}"] = float(unique_hits > 0)
        result[f"recall@{k}"] = safe_div(unique_hits, len(gold))
        result[f"precision@{k}"] = safe_div(
            sum(1 for doc_id in top_ids if doc_id in gold), len(top_ids)
        )

        dcg = sum(
            (1.0 if doc_id in gold else 0.0) / math.log2(rank + 2)
            for rank, doc_id in enumerate(top_ids)
        )
        ideal_hits = min(len(gold), k)
        idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
        result[f"ndcg@{k}"] = safe_div(dcg, idcg)

        temporal_labels = [
            item.get("temporally_valid")
            for item in top_items
            if isinstance(item.get("temporally_valid"), bool)
        ]
        if temporal_labels:
            result[f"temporal_precision@{k}"] = mean(
                float(value) for value in temporal_labels
            )

        outdated_labels = [
            item.get("outdated")
            for item in top_items
            if isinstance(item.get("outdated"), bool)
        ]
        if outdated_labels:
            result[f"outdated_rate@{k}"] = mean(
                float(value) for value in outdated_labels
            )

        distractor_labels = [
            item.get("distractor")
            for item in top_items
            if isinstance(item.get("distractor"), bool)
        ]
        if distractor_labels:
            result[f"distractor_rate@{k}"] = mean(
                float(value) for value in distractor_labels
            )
    return result


def answer_metrics(gold: dict[str, Any], run: dict[str, Any]) -> dict[str, float]:
    """Compute deterministic answer, grounding, citation and abstention metrics.

    Exact claim matching is intentionally label-driven. For semantic matching, users
    should populate ``predicted_claims`` or judge labels through an external adapter.
    """
    required = _claim_set(gold.get("required_claims", []))
    predicted_items = run.get("predicted_claims", [])
    predicted = _claim_set(predicted_items)
    claim_p, claim_r, claim_f1 = _set_prf(predicted, required)

    answerable = bool(gold.get("answerable", True))
    answer = str(run.get("answer", "")).strip()
    abstained = bool(run.get("abstained", False)) or not answer

    structured_claims = [item for item in predicted_items if isinstance(item, dict)]
    support_labels = [
        bool(item["supported"])
        for item in structured_claims
        if isinstance(item.get("supported"), bool)
    ]
    relevance_labels = [
        bool(item["relevant"])
        for item in structured_claims
        if isinstance(item.get("relevant"), bool)
    ]
    temporal_labels = [
        bool(item["temporal_correct"])
        for item in structured_claims
        if isinstance(item.get("temporal_correct"), bool)
    ]

    gold_docs = set(map(str, gold.get("gold_doc_ids", [])))
    supported_citations = 0
    total_citations = 0
    cited_required_claims: set[str] = set()
    for citation in run.get("citations", []):
        claim = normalize_text(str(citation.get("claim", "")))
        docs = set(map(str, citation.get("doc_ids", [])))
        explicit_support = citation.get("supported")
        total_citations += max(1, len(docs))
        if isinstance(explicit_support, bool):
            supported_citations += int(explicit_support)
            citation_supported = explicit_support
        else:
            supported_citations += len(docs & gold_docs)
            citation_supported = bool(docs & gold_docs)
        if claim in required and citation_supported:
            cited_required_claims.add(claim)

    citation_precision = safe_div(supported_citations, total_citations)
    citation_recall = safe_div(len(cited_required_claims), len(required))
    citation_f1 = safe_div(
        2 * citation_precision * citation_recall,
        citation_precision + citation_recall,
    )

    result = {
        "correct_abstention": float((not answerable) and abstained),
        "false_abstention": float(answerable and abstained),
        "unsafe_answer": float((not answerable) and (not abstained)),
    }
    if required:
        result.update(
            {
                "answer_claim_precision": claim_p,
                "answer_claim_recall": claim_r,
                "answer_claim_f1": claim_f1,
                "citation_precision": citation_precision,
                "citation_recall": citation_recall,
                "citation_f1": citation_f1,
            }
        )
    if gold.get("reference_answer") is not None:
        result["exact_match"] = float(
            normalize_text(answer)
            == normalize_text(str(gold.get("reference_answer", "")))
        )
    if support_labels:
        result["faithfulness"] = mean(float(v) for v in support_labels)
        result["hallucination_rate"] = 1.0 - result["faithfulness"]
    if relevance_labels:
        result["answer_relevance"] = mean(float(v) for v in relevance_labels)
    if temporal_labels:
        result["temporal_claim_accuracy"] = mean(float(v) for v in temporal_labels)
    return result


def operational_metrics(run: dict[str, Any]) -> dict[str, float]:
    result = {
        "latency_ms": float(run.get("latency_ms", 0.0) or 0.0),
        "prompt_tokens": float(run.get("prompt_tokens", 0.0) or 0.0),
        "completion_tokens": float(run.get("completion_tokens", 0.0) or 0.0),
        "estimated_cost_usd": float(run.get("estimated_cost_usd", 0.0) or 0.0),
    }
    stage_latency = run.get("stage_latency_ms", {})
    if isinstance(stage_latency, dict):
        for stage, value in stage_latency.items():
            if isinstance(value, (int, float)):
                result[f"latency.{stage}_ms"] = float(value)
    return result


def aggregate(per_query: list[dict[str, Any]]) -> dict[str, float]:
    metric_names = sorted(
        {
            name
            for row in per_query
            for name, value in row.items()
            if isinstance(value, (int, float)) and name != "query_id"
        }
    )
    result: dict[str, float] = {"query_count": float(len(per_query))}
    for name in metric_names:
        values = [
            float(row[name])
            for row in per_query
            if isinstance(row.get(name), (int, float))
        ]
        if values:
            result[name] = mean(values)

    for latency_name in [
        name
        for name in metric_names
        if name == "latency_ms" or name.startswith("latency.")
    ]:
        values = sorted(
            float(row[latency_name])
            for row in per_query
            if isinstance(row.get(latency_name), (int, float))
        )
        if values:
            base = latency_name.removesuffix("_ms")
            result[f"{base}_p50_ms"] = percentile(values, 0.50)
            result[f"{base}_p95_ms"] = percentile(values, 0.95)
    return result


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight
