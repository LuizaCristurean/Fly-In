# Map used by "make run" and "make debug" (override with MAP=...).
MAP ?= maps/easy/01_linear_path.txt

.PHONY: install run debug clean lint lint-strict test

install:
	uv sync

run:
	uv run python main.py $(MAP)

debug:
	uv run python -m pdb main.py $(MAP)

clean:
	find . -path ./.venv -prune -o -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

test:
	uv run python -m pytest tests -q