UV = uv
VENV = .venv
FLAKE8 := .venv/bin/flake8
MYPY := .venv/bin/mypy
MAP ?= test.txt
ARGS ?=
MYPYFLAGS = --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

export UV_LINK_MODE = copy

.PHONY: install run debug clean lint lint-strict

install: $(VENV)
	$(UV) sync
	$(UV) pip install flake8 mypy

run:
	$(UV) run fly_in.py $(MAP) $(ARGS)

debug:
	$(UV) run -m pdb fly_in.py $(MAP) $(ARGS)

$(VENV):
	uv venv $(VENV)

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

fclean: clean
	rm -rf $(VENV)

lint:
	$(UV) run $(FLAKE8) .
	$(UV) run $(MYPY) . $(MYPYFLAGS)

lint-strict:
	$(UV) run $(FLAKE8) .
	$(UV) run $(MYPY) . --strict
