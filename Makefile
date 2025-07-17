SHELL = /bin/bash

PYTHON = python3

unittest:
	@$(PYTHON) -m unittest tests/**
.PHONY: unittest
