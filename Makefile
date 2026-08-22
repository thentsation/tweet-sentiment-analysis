.PHONY: install run run-full test coverage lint format typecheck docker-build docker-run clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r config/requirements.txt
	$(PIP) install -r config/requirements-dev.txt

SAMPLE ?= 2000

run:
	$(PYTHON) src/main.py --sample $(SAMPLE)

run-full:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

typecheck:
	$(VENV)/bin/mypy

docker-build:
	docker build -f docker/Dockerfile -t tweet-sentiment .

docker-run:
	docker run --rm -v $(shell pwd)/reports:/app/reports tweet-sentiment

clean:
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type d -name .pytest_cache -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type d -name .ruff_cache -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type d -name .mypy_cache -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type f -name '*.pyc' -not -path './$(VENV)/*' -delete
	rm -f .coverage
	rm -rf reports
