.PHONY: help install install-dev test lint format type-check clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo "  make clean         - Clean build artifacts"

install:
	uv sync

install-dev:
	uv sync --dev
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run black .
	uv run ruff check . --fix

type-check:
	uv run mypy oryx_wat_scraper

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf outputfiles/
