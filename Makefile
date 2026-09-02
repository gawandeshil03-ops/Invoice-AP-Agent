.DEFAULT_GOAL := help
PY ?= python3.12

.PHONY: help setup install dev lint fmt test run eval report demo clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtualenv (Python 3.12)
	$(PY) -m venv .venv

install: ## Install the package
	. .venv/bin/activate && pip install -e .

dev: setup ## Create venv + install with dev extras
	. .venv/bin/activate && pip install -e ".[dev]"

lint: ## Ruff lint + format check
	. .venv/bin/activate && ruff check . && ruff format --check .

fmt: ## Auto-format with ruff
	. .venv/bin/activate && ruff format . && ruff check --fix .

test: ## Run the test suite
	. .venv/bin/activate && pytest -q

run: ## Process every invoice and print decisions
	. .venv/bin/activate && ap-agent run

eval: ## Run the evaluation suite + safety gate
	. .venv/bin/activate && ap-agent eval

report: ## Regenerate the example audit report
	. .venv/bin/activate && ap-agent eval --report reports/audit_report_example.md

demo: ## Process a few invoices
	. .venv/bin/activate && ap-agent demo

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
