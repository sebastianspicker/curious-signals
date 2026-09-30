.PHONY: help lint test test-browser validate check-generated build provision compile security ci bundle
.DEFAULT_GOAL := help

PYTHON ?= python3
TOOL = PYTHONPATH=src $(PYTHON) -m curious_signals
PYTEST = PYTHONPATH=src $(PYTHON) -m pytest
RUFF = $(PYTHON) -m ruff

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check"
	@echo "  test     - Python test suite"
	@echo "  test-browser - Preview interaction and accessibility checks (Chromium)"
	@echo "  validate - Validate XML and phyphox files"
	@echo "  check-generated - Verify tracked experiments match their sources"
	@echo "  build    - Rebuild experiments/*.phyphox from src/phyphox/*.phyphox.xml"
	@echo "  provision - Install pinned Arduino core and libraries (network)"
	@echo "  compile  - Verify installed pins and compile Arduino sketch (no installs/upload)"
	@echo "  security - Secret scan plus dependency, shell, and Python sanity checks"
	@echo "  ci       - Run the full checkout-non-mutating local gate"
	@echo "  bundle   - Build and zip the seven core sensor experiments"

lint:
	$(RUFF) check .
	$(RUFF) format --check .

test:
	$(PYTEST)

test-browser:
	$(PYTEST) -m browser

validate:
	$(TOOL) validate

check-generated:
	$(TOOL) check-generated

build:
	$(TOOL) build

compile:
	./scripts/compile-arduino.sh

provision:
	$(PYTHON) scripts/arduino_toolchain.py provision

security:
	bash scripts/security.sh

ci:
	+$(MAKE) --no-print-directory lint
	+$(MAKE) --no-print-directory test
	+$(MAKE) --no-print-directory test-browser
	+$(MAKE) --no-print-directory validate
	+$(MAKE) --no-print-directory check-generated
	+$(MAKE) --no-print-directory provision
	+$(MAKE) --no-print-directory compile
	+$(MAKE) --no-print-directory security

bundle:
	$(TOOL) bundle
