.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/python -m src

debug:
	.venv/bin/python -m pdb -m src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 --exclude .venv .
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude ".venv" --follow-imports=skip .

lint-strict:
	flake8 --exclude .venv .
	mypy --strict --exclude ".venv" --follow-imports=skip .