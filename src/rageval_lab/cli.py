from __future__ import annotations

import argparse
import json
from pathlib import Path

from .calibration import calibrate_binary
from .diagnostics import diagnose_conditions
from .evaluate import evaluate
from .io import read_jsonl, write_json, write_jsonl
from .manifest import create_manifest
from .report import render_markdown
from .stats import (
    bootstrap_ci,
    effect_size,
    holm_adjust,
    paired_differences,
    sign_flip_pvalue,
)
from .validate import validate_rows


def _parse_ks(value: str) -> list[int]:
    try:
        ks = sorted({int(item) for item in value.split(",") if item.strip()})
    except ValueError as exc:
        raise argparse.ArgumentTypeError("K values must be integers") from exc
    if not ks or min(ks) < 1:
        raise argparse.ArgumentTypeError("K values must be positive integers")
    return ks


def _parse_metrics(value: str) -> list[str]:
    metrics = [item.strip() for item in value.split(",") if item.strip()]
    if not metrics:
        raise argparse.ArgumentTypeError("At least one metric is required")
    return metrics


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_rows(read_jsonl(args.gold), read_jsonl(args.run), strict=args.strict)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Validation passed.")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    gold = read_jsonl(args.gold)
    run = read_jsonl(args.run)
    errors = validate_rows(gold, run, strict=args.strict)
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))
    summary, per_query = evaluate(gold, run, args.ks)
    output = Path(args.output)
    payload = {
        "summary": summary,
        "manifest": create_manifest([args.gold, args.run], {"ks": args.ks}),
    }
    write_json(output, payload)
    per_query_path = output.with_suffix(".per_query.jsonl")
    report_path = output.with_suffix(".md")
    write_jsonl(per_query_path, per_query)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote {output}, {per_query_path}, and {report_path}")
    return 0


def _metric_comparison(
    a: dict[str, dict],
    b: dict[str, dict],
    shared_query_ids: list[str],
    metric: str,
    args: argparse.Namespace,
) -> dict[str, object]:
    """Compare one metric using only query pairs where both values are numeric.

    RAG benchmarks often contain heterogeneous labels. For example, an
    unanswerable query may legitimately omit answer-claim metrics. Pairwise
    deletion is therefore applied independently per metric and is reported in
    the output instead of silently imputing a zero or failing the whole run.
    """
    query_ids = [
        query_id
        for query_id in shared_query_ids
        if isinstance(a[query_id].get(metric), (int, float))
        and isinstance(b[query_id].get(metric), (int, float))
    ]
    if not query_ids:
        raise ValueError(
            f"Metric {metric!r} has no shared numeric observations in the two runs"
        )

    a_values = [float(a[query_id][metric]) for query_id in query_ids]
    b_values = [float(b[query_id][metric]) for query_id in query_ids]
    differences = paired_differences(a_values, b_values)
    low, high = bootstrap_ci(differences, args.iterations, args.seed)
    return {
        "metric": metric,
        "n": len(query_ids),
        "excluded_shared_queries": len(shared_query_ids) - len(query_ids),
        "mean_a": sum(a_values) / len(a_values),
        "mean_b": sum(b_values) / len(b_values),
        "mean_delta_b_minus_a": sum(differences) / len(differences),
        "bootstrap_95_ci": [low, high],
        "sign_flip_p": sign_flip_pvalue(differences, args.iterations, args.seed),
        "paired_effect_size_dz": effect_size(differences),
    }


def cmd_compare(args: argparse.Namespace) -> int:
    a = {str(row["query_id"]): row for row in read_jsonl(args.run_a)}
    b = {str(row["query_id"]): row for row in read_jsonl(args.run_b)}
    query_ids = sorted(set(a) & set(b))
    if not query_ids:
        raise SystemExit("No shared query_ids")
    results = [
        _metric_comparison(a, b, query_ids, metric, args) for metric in args.metrics
    ]
    adjusted = holm_adjust([float(item["sign_flip_p"]) for item in results])
    for item, p_adjusted in zip(results, adjusted):
        item["holm_adjusted_p"] = p_adjusted
    payload = {"shared_queries": len(query_ids), "comparisons": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.output:
        write_json(args.output, payload)
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    summary, details = diagnose_conditions(
        read_jsonl(args.base),
        read_jsonl(args.oracle),
        read_jsonl(args.retrieved),
        args.metric,
        args.pass_threshold,
    )
    payload = {"metric": args.metric, "summary": summary}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.output:
        output = Path(args.output)
        write_json(output, payload)
        write_jsonl(output.with_suffix(".per_query.jsonl"), details)
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    result = calibrate_binary(read_jsonl(args.labels))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        write_json(args.output, result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rageval", description="Framework-agnostic RAG evaluation toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate gold and run JSONL")
    validate.add_argument("gold")
    validate.add_argument("run")
    validate.add_argument("--strict", action="store_true")
    validate.set_defaults(func=cmd_validate)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="compute metrics and generate JSON/JSONL/Markdown reports"
    )
    evaluate_parser.add_argument("gold")
    evaluate_parser.add_argument("run")
    evaluate_parser.add_argument("--ks", type=_parse_ks, default=[1, 3, 5, 10])
    evaluate_parser.add_argument("--output", default="results/evaluation.json")
    evaluate_parser.add_argument("--strict", action="store_true")
    evaluate_parser.set_defaults(func=cmd_evaluate)

    compare = subparsers.add_parser(
        "compare", help="paired comparison with CI, sign-flip tests and Holm correction"
    )
    compare.add_argument("run_a")
    compare.add_argument("run_b")
    compare.add_argument(
        "--metrics", type=_parse_metrics, required=True, help="comma-separated metrics"
    )
    compare.add_argument("--iterations", type=int, default=5000)
    compare.add_argument("--seed", type=int, default=7)
    compare.add_argument("--output")
    compare.set_defaults(func=cmd_compare)

    diagnose = subparsers.add_parser(
        "diagnose", help="diagnose Base/Oracle/Retrieved context conditions"
    )
    diagnose.add_argument("base")
    diagnose.add_argument("oracle")
    diagnose.add_argument("retrieved")
    diagnose.add_argument("--metric", default="answer_claim_f1")
    diagnose.add_argument("--pass-threshold", type=float, default=0.8)
    diagnose.add_argument("--output")
    diagnose.set_defaults(func=cmd_diagnose)

    calibrate = subparsers.add_parser(
        "calibrate", help="measure binary model-judge agreement with human labels"
    )
    calibrate.add_argument("labels")
    calibrate.add_argument("--output")
    calibrate.set_defaults(func=cmd_calibrate)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
