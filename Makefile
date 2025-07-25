SHELL = /bin/bash

clean-cache:
	@find . -path './app/**/__pycache__/**' -delete
	@find . -path './app/**/__pycache__' -delete
.PHONY: clean-cache

unit-test:
	@set -e
	@./scripts/unit-test.sh
	@make clean-cache
.PHONY: unit-test
