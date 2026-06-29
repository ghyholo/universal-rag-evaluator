from __future__ import annotations

from statistics import mean
from typing import Any


def diagnose_conditions(
    base_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    retrieved_rows: list[dict[str, Any]],
    metric: str,
    pass_threshold: float = 0.8,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    base = {str(row["query_id"]): row for row in base_rows}
    oracle = {str(row["query_id"]): row for row in oracle_rows}
    retrieved = {str(row["query_id"]): row for row in retrieved_rows}
    query_ids = sorted(set(base) & set(oracle) & set(retrieved))
    if not query_ids:
        raise ValueError("No query_ids shared by Base, Oracle and Retrieved files")

    details: list[dict[str, Any]] = []
    for query_id in query_ids:
        try:
            b = float(base[query_id][metric])
            o = float(oracle[query_id][metric])
            r = float(retrieved[query_id][metric])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"query {query_id}: missing or invalid metric {metric}") from exc

        if o < pass_threshold:
            label = "generator_or_task_failure"
        elif r < pass_threshold and o >= pass_threshold:
            label = "retrieval_or_context_failure"
        elif r < b:
            label = "context_harm"
        else:
            label = "pass"
        details.append(
            {
                "query_id": query_id,
                "base": b,
                "oracle": o,
                "retrieved": r,
                "oracle_gain_over_base": o - b,
                "retrieval_gain_over_base": r - b,
                "retrieval_loss_vs_oracle": o - r,
                "diagnosis": label,
            }
        )

    return {
        "n": float(len(details)),
        "base_mean": mean(row["base"] for row in details),
        "oracle_mean": mean(row["oracle"] for row in details),
        "retrieved_mean": mean(row["retrieved"] for row in details),
        "oracle_gain_over_base": mean(
            row["oracle_gain_over_base"] for row in details
        ),
        "retrieval_gain_over_base": mean(
            row["retrieval_gain_over_base"] for row in details
        ),
        "retrieval_loss_vs_oracle": mean(
            row["retrieval_loss_vs_oracle"] for row in details
        ),
        "context_harm_rate": mean(
            float(row["diagnosis"] == "context_harm") for row in details
        ),
        "retrieval_failure_rate": mean(
            float(row["diagnosis"] == "retrieval_or_context_failure")
            for row in details
        ),
        "generator_failure_rate": mean(
            float(row["diagnosis"] == "generator_or_task_failure")
            for row in details
        ),
    }, details
