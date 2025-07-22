SHELL = /bin/bash

PYTHON = python3
COVERAGE = $(PYTHON) -m coverage

.venv:
	@$(PYTHON) venv --help 2>&1 > /dev/null \
		|| $(PYTHON) -m pip install venv
	@$(PYTHON) -m venv .venv

unit-test: .venv
	@source .venv/bin/activate
	@$(COVERAGE) --help > /dev/null \
		|| $(PYTHON) -m pip install coverage
	
	@$(COVERAGE) run -m unittest discover
.PHONY: unit-test
