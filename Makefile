# Vitruvyan Core — Developer commands
# Usage: make <target>

.PHONY: help test lint format check clean build install dev

PYTHON   ?= python3
PYTEST   ?= $(PYTHON) -m pytest
RUFF     ?= $(PYTHON) -m ruff
BLACK    ?= $(PYTHON) -m black
MYPY     ?= $(PYTHON) -m mypy

SRC      := vitruvyan_core
TESTS    := tests
COV_MIN  := 75

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────────────────

install: ## Install package in editable mode with dev deps
	$(PYTHON) -m pip install -e ".[dev]"

dev: install ## Install + set up pre-commit hooks
	$(PYTHON) -m pip install pre-commit
	pre-commit install

# ── Quality ──────────────────────────────────────────────────────────────

lint: ## Run ruff linter
	$(RUFF) check $(SRC) $(TESTS) services/

format: ## Auto-format code (black + ruff)
	$(BLACK) --line-length 100 $(SRC) $(TESTS) services/
	$(RUFF) check --fix $(SRC) $(TESTS) services/

check: lint ## Lint + type check (contracts + agents)
	$(MYPY) $(SRC)/contracts/ $(SRC)/core/agents/ --ignore-missing-imports

# ── Testing ──────────────────────────────────────────────────────────────

test: ## Run unit + integration tests (no e2e)
	$(PYTEST) -m "not e2e" $(TESTS)/

test-all: ## Run all tests including e2e
	$(PYTEST) $(TESTS)/

test-arch: ## Run architectural guardrail tests
	$(PYTEST) $(TESTS)/architectural/ -m architectural -q

test-cov: ## Run tests with coverage report
	$(PYTEST) -m "not e2e" --cov=$(SRC) --cov-report=term-missing --cov-fail-under=$(COV_MIN) $(TESTS)/

smoke: ## Run smoke tests
	bash smoke_tests/run.sh

# ── Docker ───────────────────────────────────────────────────────────────

build: ## Build all Docker services
	cd infrastructure/docker && docker compose build

up: ## Start full stack
	cd infrastructure/docker && docker compose up -d

down: ## Stop full stack
	cd infrastructure/docker && docker compose down

health: ## Check health of all running containers
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "core_|NAMES"

logs: ## Tail logs (usage: make logs s=graph)
	docker logs core_$(s) --tail=50 -f

# ── Cleanup ──────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info htmlcov/ .coverage
