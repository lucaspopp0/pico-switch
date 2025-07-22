SHELL = /bin/bash

PYTHON = python3
COVERAGE = $(PYTHON) -m coverage

clean-cache:
	@rm -rf ./**/__pycache__
.PHONY: clean-cache

unit-test:
	@set -e
	@$(COVERAGE) --help 2>&1 > /dev/null \
		|| $(PYTHON) -m pip install coverage
	
	@$(COVERAGE) run -m unittest
	
	@$(COVERAGE) report
	@$(COVERAGE) xml

	@make clean-cache
.PHONY: unit-test
