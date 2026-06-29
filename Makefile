.PHONY: install test smoke clean

install:
	python -m pip install -e .

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

smoke:
	rageval validate examples/gold.jsonl examples/run_a.jsonl --strict
	rageval evaluate examples/gold.jsonl examples/run_a.jsonl --output results/run_a.json
	rageval calibrate examples/judge_labels.jsonl

clean:
	rm -rf build dist results .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
