from __future__ import annotations

from typing import Any


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_rows(
    gold: list[dict[str, Any]], run: list[dict[str, Any]], strict: bool = False
) -> list[str]:
    errors: list[str] = []
    gold_ids = [str(row.get("query_id", "")) for row in gold]
    run_ids = [str(row.get("query_id", "")) for row in run]

    for idx, row in enumerate(gold, start=1):
        prefix = f"gold row {idx}"
        if not row.get("query_id"):
            errors.append(f"{prefix}: missing query_id")
        if not row.get("question"):
            errors.append(f"{prefix}: missing question")
        if "answerable" not in row or not isinstance(row.get("answerable"), bool):
            errors.append(f"{prefix}: answerable must be a boolean")
        if row.get("answerable") and not (
            row.get("gold_doc_ids") or row.get("required_claims")
        ):
            errors.append(
                f"{prefix}: answerable query has no gold evidence or required claims"
            )
        if not isinstance(row.get("gold_doc_ids", []), list):
            errors.append(f"{prefix}: gold_doc_ids must be a list")
        if not isinstance(row.get("required_claims", []), list):
            errors.append(f"{prefix}: required_claims must be a list")
        if not isinstance(row.get("slices", {}), dict):
            errors.append(f"{prefix}: slices must be an object")

    for idx, row in enumerate(run, start=1):
        prefix = f"run row {idx}"
        if not row.get("query_id"):
            errors.append(f"{prefix}: missing query_id")
        if "answer" not in row:
            errors.append(f"{prefix}: missing answer")
        retrieved = row.get("retrieved", [])
        if not isinstance(retrieved, list):
            errors.append(f"{prefix}: retrieved must be a list")
            continue
        doc_ids: list[str] = []
        ranks: list[int] = []
        for item_index, item in enumerate(retrieved, start=1):
            if not isinstance(item, dict):
                errors.append(f"{prefix}: retrieved item {item_index} must be an object")
                continue
            if not item.get("doc_id"):
                errors.append(f"{prefix}: retrieved item {item_index} missing doc_id")
            doc_ids.append(str(item.get("doc_id", "")))
            if "rank" in item:
                if not isinstance(item["rank"], int) or item["rank"] < 1:
                    errors.append(
                        f"{prefix}: retrieved item {item_index} rank must be a positive integer"
                    )
                else:
                    ranks.append(item["rank"])
        duplicate_docs = _duplicates(doc_ids)
        if duplicate_docs:
            errors.append(f"{prefix}: duplicate retrieved doc_ids: {duplicate_docs}")
        if strict and ranks and ranks != list(range(1, len(ranks) + 1)):
            errors.append(f"{prefix}: ranks must be contiguous and ordered from 1")

        for field in [
            "latency_ms",
            "prompt_tokens",
            "completion_tokens",
            "estimated_cost_usd",
        ]:
            if field in row and (
                not isinstance(row[field], (int, float)) or row[field] < 0
            ):
                errors.append(f"{prefix}: {field} must be a non-negative number")

    for duplicate in _duplicates(gold_ids):
        errors.append(f"duplicate gold query_id: {duplicate}")
    for duplicate in _duplicates(run_ids):
        errors.append(f"duplicate run query_id: {duplicate}")

    missing = sorted(set(gold_ids) - set(run_ids))
    extra = sorted(set(run_ids) - set(gold_ids))
    if missing:
        errors.append(f"run is missing query_ids: {missing}")
    if strict and extra:
        errors.append(f"run has unknown query_ids: {extra}")
    return errors
