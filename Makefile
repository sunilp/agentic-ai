.PHONY: install test lint eval run clean serve build-site deploy compare-multiagent foundations foundations-compare lab-002-data lab-002-run lab-002-eval

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

eval:
	python project/doc-intelligence-agent/evals/run_eval.py

run:
	python src/ch02/run.py

compare:
	python src/ch03/compare.py

compare-multiagent:
	python -m src.ch04_multiagent.run --docs docs/book/ --query "What is multi-agent?"

serve:
	mkdocs serve

build-site:
	mkdocs build --strict

deploy:
	mkdocs gh-deploy --force

typecheck:
	mypy src/ --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache

foundations:
	python src/ch00/llm_basics.py
	python src/ch00/tool_use.py
	python src/ch00/raw_agent.py

foundations-compare:
	python src/ch00/eval_compare.py

lab-002-data:
	python -m labs.lab_002.dataset 30

lab-002-run:
	python -m labs.lab_002.run

lab-002-eval:
	python -m labs.lab_002.evaluate
