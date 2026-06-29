# Contributing

1. Create a focused branch.
2. Add or update tests for every metric change.
3. Preserve backwards compatibility of the JSONL contract when possible.
4. Run `python -m unittest discover -s tests -v`.
5. Explain statistical or semantic assumptions in the pull request.

Do not add a mandatory external LLM dependency to the deterministic core. Model judges should remain optional adapters.
