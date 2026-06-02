PYTHON ?= python3

.PHONY: check
check:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) scripts/check_portfolio_readme.py
