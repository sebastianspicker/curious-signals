.PHONY: help lint test validate check-generated build compile security ci ci-local bundle
.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check"
	@echo "  test     - Python test suite"
	@echo "  validate - Validate XML and phyphox files"
	@echo "  check-generated - Verify tracked experiments match their sources"
	@echo "  build    - Rebuild experiments/*.phyphox from src/phyphox/*.phyphox.xml"
	@echo "  compile  - Compile Arduino sketch (arduino-cli, no upload)"
	@echo "  security - Secret scan, dependency pin check, minimal SAST"
	@echo "  ci       - Run lint, test, validate, generated check, compile, security"
	@echo "  ci-local - Run the canonical local CI entrypoint"
	@echo "  bundle   - Build and zip the seven core sensor experiments"

lint:
	ruff check .
	ruff format --check .

test:
	pytest

validate:
	./scripts/validate-xml.sh

check-generated:
	bash scripts/check-generated-clean.sh

build:
	./scripts/build-phyphox.sh

compile:
	./scripts/compile-arduino.sh

security:
	bash scripts/test-shell-guardrails.sh
	./scripts/secret-scan.sh
	./scripts/deps-scan.sh
	./scripts/sast-minimal.sh

ci: lint test validate check-generated build compile security

ci-local:
	./scripts/ci-local.sh

bundle: build
	@zip -q -j phyphox-experiments.zip experiments/*.phyphox && echo "Created phyphox-experiments.zip"
