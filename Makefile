PYTHON ?= python3

.PHONY: check
check:
	$(PYTHON) scripts/check_portfolio_readme.py
