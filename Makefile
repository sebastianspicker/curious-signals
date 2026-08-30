.PHONY: help lint test validate check-generated build compile security ci bundle
.DEFAULT_GOAL := help

PYTHON ?= python3
TOOL = PYTHONPATH=src $(PYTHON) -m curious_signals
PYTEST = PYTHONPATH=src $(PYTHON) -m pytest
RUFF = $(PYTHON) -m ruff

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check"
	@echo "  test     - Python test suite"
	@echo "  validate - Validate XML and phyphox files"
	@echo "  check-generated - Verify tracked experiments match their sources"
	@echo "  build    - Rebuild experiments/*.phyphox from src/phyphox/*.phyphox.xml"
	@echo "  compile  - Compile Arduino sketch (arduino-cli, no upload)"
	@echo "  security - Secret scan plus dependency, shell, and Python sanity checks"
	@echo "  ci       - Run the full checkout-non-mutating local gate"
	@echo "  bundle   - Build and zip the seven core sensor experiments"

lint:
	$(RUFF) check .
	$(RUFF) format --check .

test:
	$(PYTEST)

validate:
	$(TOOL) validate

check-generated:
	$(TOOL) check-generated

build:
	$(TOOL) build

compile:
	./scripts/compile-arduino.sh

security:
	bash scripts/security.sh

ci:
	+$(MAKE) --no-print-directory lint
	+$(MAKE) --no-print-directory test
	+$(MAKE) --no-print-directory validate
	+$(MAKE) --no-print-directory check-generated
	+$(MAKE) --no-print-directory compile
	+$(MAKE) --no-print-directory security

bundle:
	$(TOOL) bundle
