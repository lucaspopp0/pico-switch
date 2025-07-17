SHELL = /bin/bash

PYTHON = python3

unit-test:
	@$(PYTHON) -m unittest tests/**
.PHONY: unit-test
