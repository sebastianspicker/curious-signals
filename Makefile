.PHONY: help lint validate check-generated build provision compile security ci bundle
.DEFAULT_GOAL := help

PYTHON ?= python3
TOOL = PYTHONPATH=src $(PYTHON) -m curious_signals
RUFF = $(PYTHON) -m ruff

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check, shellcheck"
	@echo "  validate - Validate XML and phyphox files"
	@echo "  check-generated - Verify tracked experiments match their sources"
	@echo "  build    - Rebuild experiments/*.phyphox from src/phyphox/*.phyphox.xml"
	@echo "  provision - Install pinned Arduino core and libraries (network)"
	@echo "  compile  - Verify installed pins and compile Arduino sketch (no installs/upload)"
	@echo "  security - Credential scan of tracked and untracked files"
	@echo "  ci       - Run the full checkout-non-mutating local gate"
	@echo "  bundle   - Build and zip the seven core sensor experiments"

lint:
	$(RUFF) check .
	$(RUFF) format --check .
	shellcheck scripts/*.sh

validate:
	$(TOOL) validate

check-generated:
	$(TOOL) check-generated

build:
	$(TOOL) build

compile:
	$(TOOL) compile

provision:
	$(TOOL) provision

security:
	bash scripts/secret-scan.sh

ci:
	+$(MAKE) --no-print-directory lint
	+$(MAKE) --no-print-directory validate
	+$(MAKE) --no-print-directory check-generated
	+$(MAKE) --no-print-directory provision
	+$(MAKE) --no-print-directory compile
	+$(MAKE) --no-print-directory security

bundle:
	$(TOOL) bundle
