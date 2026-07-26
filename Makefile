PYTHON := .venv/bin/python
VENV = .venv
FLAKE8 := .venv/bin/flake8
MYPY := .venv/bin/mypy
MYPYFLAGS = --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

export UV_LINK_MODE = copy

.PHONY: install run debug clean lint lint-strict test

install: $(VENV)
	uv sync
	uv pip install flake8 mypy

run:
	$(PYTHON) fly_in.py

debug:
	$(PYTHON) -m pdb fly_in.py

$(VENV):
	uv venv $(VENV)

clean:
	rm -rf .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

lint:
	$(FLAKE8) .
	$(MYPY) . $(MYPYFLAGS)

lint-strict:
	$(FLAKE8) .
	$(MYPY) . --strict

test:
	$(PYTHON) -m pytest -q
