from __future__ import annotations

from typing import Any


def render_markdown(summary: dict[str, Any], title: str = "RAG Evaluation Report") -> str:
    lines = [
        f"# {title}",
        "",
        "## Overall metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in sorted(summary.items()):
        if key == "slices" or not isinstance(value, (int, float)):
            continue
        lines.append(f"| `{key}` | {value:.6f} |")

    slices = summary.get("slices", {})
    if isinstance(slices, dict) and slices:
        lines.extend(["", "## Slice analysis"])
        for dimension, groups in sorted(slices.items()):
            lines.extend(
                [
                    "",
                    f"### {dimension}",
                    "",
                    "| Slice | Queries | Claim F1 | Recall@5 | Latency p95 (ms) |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for value, metrics in sorted(groups.items()):
                lines.append(
                    f"| {value} | {metrics.get('query_count', 0):.0f} | "
                    f"{metrics.get('answer_claim_f1', 0):.4f} | "
                    f"{metrics.get('recall@5', 0):.4f} | "
                    f"{metrics.get('latency_p95_ms', 0):.2f} |"
                )
    lines.append("")
    return "\n".join(lines)
