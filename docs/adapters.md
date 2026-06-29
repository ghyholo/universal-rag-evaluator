# Adapter guide

The evaluator is deliberately framework-independent. An adapter only needs to export JSONL rows.

## Generic Python example

```python
import json
from pathlib import Path


def export_run(system, benchmark, output_path: str) -> None:
    path = Path(output_path)
    with path.open("w", encoding="utf-8") as handle:
        for example in benchmark:
            result = system.ask(example["question"])
            row = {
                "query_id": example["query_id"],
                "answer": result.answer,
                "retrieved": [
                    {
                        "doc_id": item.id,
                        "rank": rank,
                        "score": item.score,
                        "text": item.text,
                    }
                    for rank, item in enumerate(result.sources, start=1)
                ],
                "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
```

## Production systems

For a remote API or non-Python stack, export the same fields from logs. Do not expose secrets, user identifiers, or unredacted private text in a public benchmark.
