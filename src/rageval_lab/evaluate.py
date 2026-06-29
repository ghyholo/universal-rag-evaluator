from __future__ import annotations

from collections import defaultdict
from typing import Any

from .metrics import aggregate, answer_metrics, operational_metrics, retrieval_metrics


def evaluate(
    gold_rows: list[dict[str, Any]], run_rows: list[dict[str, Any]], ks: list[int]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_by_id = {str(row["query_id"]): row for row in run_rows}
    per_query: list[dict[str, Any]] = []
    for gold in gold_rows:
        query_id = str(gold["query_id"])
        run = run_by_id[query_id]
        row: dict[str, Any] = {"query_id": query_id}
        row.update(
            retrieval_metrics(gold.get("gold_doc_ids", []), run.get("retrieved", []), ks)
        )
        row.update(answer_metrics(gold, run))
        row.update(operational_metrics(run))
        slices = gold.get("slices", {})
        if isinstance(slices, dict):
            for key, value in slices.items():
                row[f"slice.{key}"] = value
        per_query.append(row)

    summary: dict[str, Any] = aggregate(per_query)
    summary["slices"] = slice_aggregates(per_query)
    return summary, per_query


def slice_aggregates(per_query: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in per_query:
        for key, value in row.items():
            if key.startswith("slice."):
                groups[key.removeprefix("slice.")][str(value)].append(row)
    return {
        dimension: {
            value: aggregate(rows) for value, rows in sorted(value_groups.items())
        }
        for dimension, value_groups in sorted(groups.items())
    }
