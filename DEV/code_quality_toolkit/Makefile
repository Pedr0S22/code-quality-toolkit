PYTHON := python
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup lint format typecheck test run report clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .[dev]

lint:
	$(BIN)/ruff check src tests

format:
	$(BIN)/black src tests

typecheck:
	$(BIN)/mypy src/toolkit

test:
	$(BIN)/pytest

run:
	$(BIN)/python -m toolkit.core.cli analyze examples/sample_project --out report.json

report: run

clean:
	rm -rf $(VENV) report.json .mypy_cache .pytest_cache
