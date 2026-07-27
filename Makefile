<<<<<<< HEAD
.PHONY: help lint test validate generated-clean build compile security ci ci-local bundle
=======
.PHONY: help lint test validate check-generated build compile security ci ci-local bundle
>>>>>>> dev
.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  lint     - Ruff lint + format check"
	@echo "  test     - Python test suite"
	@echo "  validate - Validate XML and phyphox files"
<<<<<<< HEAD
	@echo "  generated-clean - Verify generated experiments are current"
=======
	@echo "  check-generated - Verify tracked experiments match their sources"
>>>>>>> dev
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

<<<<<<< HEAD
generated-clean:
=======
check-generated:
>>>>>>> dev
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

<<<<<<< HEAD
ci: lint test validate generated-clean build compile security
=======
ci: lint test validate check-generated compile security
>>>>>>> dev

ci-local:
	./scripts/ci-local.sh

bundle: build
	@zip -q -j phyphox-experiments.zip experiments/*.phyphox && echo "Created phyphox-experiments.zip"
