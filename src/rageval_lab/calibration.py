from __future__ import annotations

from typing import Any

from .metrics import safe_div


def calibrate_binary(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Compare binary model-judge labels with human labels."""
    pairs: list[tuple[bool, bool]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row.get("human_label"), bool):
            raise ValueError(f"row {index}: human_label must be boolean")
        if not isinstance(row.get("judge_label"), bool):
            raise ValueError(f"row {index}: judge_label must be boolean")
        pairs.append((row["human_label"], row["judge_label"]))
    if not pairs:
        raise ValueError("calibration file is empty")

    tp = sum(h and j for h, j in pairs)
    tn = sum((not h) and (not j) for h, j in pairs)
    fp = sum((not h) and j for h, j in pairs)
    fn = sum(h and (not j) for h, j in pairs)
    n = len(pairs)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    observed = safe_div(tp + tn, n)
    human_positive = safe_div(tp + fn, n)
    judge_positive = safe_div(tp + fp, n)
    expected = human_positive * judge_positive + (1 - human_positive) * (
        1 - judge_positive
    )
    kappa = safe_div(observed - expected, 1 - expected)
    return {
        "n": float(n),
        "accuracy": observed,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "cohen_kappa": kappa,
        "tp": float(tp),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
    }
