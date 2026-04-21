.PHONY: help lint test validate build compile security ci ci-local bundle
.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check"
	@echo "  test     - Python test suite"
	@echo "  validate - Validate XML and phyphox files"
	@echo "  build    - Rebuild experiments/*.phyphox from src/phyphox/*.phyphox.xml"
	@echo "  compile  - Compile Arduino sketch (arduino-cli, no upload)"
	@echo "  security - Secret scan, dependency pin check, minimal SAST"
	@echo "  ci       - Run lint, test, validate, build, compile, security"
	@echo "  ci-local - Run the canonical local CI entrypoint"
	@echo "  bundle   - Build experiments/*.phyphox and zip to phyphox-experiments.zip"

lint:
	ruff check .
	ruff format --check .

test:
	pytest

validate:
	./scripts/validate-xml.sh

build:
	./scripts/build-phyphox.sh

compile:
	./scripts/compile-arduino.sh

security:
	./scripts/secret-scan.sh
	./scripts/deps-scan.sh
	./scripts/sast-minimal.sh

ci: lint test validate build compile security

ci-local:
	./scripts/ci-local.sh

bundle: build
	@zip -q -j phyphox-experiments.zip experiments/*.phyphox && echo "Created phyphox-experiments.zip"
