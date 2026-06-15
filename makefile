.PHONY: help install lint format test build run-local pipeline-all

.DEFAULT_GOAL := help

help:
	@echo "Commandes disponibles :"
	@echo "  make install       - Install local environment with uv"
	@echo "  make lint          - Check quality code with ruff"
	@echo "  make format        - Format with ruff"
	@echo "  make test          - Launch test with pytest"
	@echo "  make build         - Build docker image for local execution"
	@echo "  make run-local     - Launch docker image with local .env"
	@echo "  make pipeline-all  - format, lint, test, build and run"

# --- LOCAL ENVIRONMENT ---
install:
	uv sync

# --- CODE QUALITY ---
lint-and-format:
	uv run ruff check . --fix & uv run ruff format .

test:
	uv run ruff format --check .
	uv run ruff check .
	uv run pytest

# --- DOCKER ---
build:
	docker build -t energy-pipeline .

run-local:
	docker run --rm --env-file .env energy-pipeline

# --- COMPLETE WORKFLOW ---
pipeline-all: format lint test build run-local