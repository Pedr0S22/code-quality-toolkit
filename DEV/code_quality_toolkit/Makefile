PYTHON := python
VENV := .venv

# If Windows, then use 'Scripts', else use 'bin'
ifeq ($(OS),Windows_NT)
    BIN_DIR := $(VENV)/Scripts
else
    BIN_DIR := $(VENV)/bin
endif

BIN := $(BIN_DIR)

.PHONY: setup lint format typecheck test run report clean

# Use of "python -m"
setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e .[dev]

lint:
	$(BIN)/ruff check src tests

lint_fix:
	$(BIN)/ruff check --fix src tests

format:
	$(BIN)/black src tests

typecheck:
	$(BIN)/mypy src/toolkit

test:
	$(BIN)/pytest $(DIR)

run:
	$(BIN)/python -m toolkit.core.cli analyze examples/sample_project --out report.json --config toolkit.toml $(arg)

report: run

clean:
	rm -rf $(VENV) report.json .mypy_cache .pytest_cache
