.PHONY: test cov clean install help

help:
	@echo "Available targets:"
	@echo "  test     - Run tests with pytest"
	@echo "  cov      - Run tests with coverage report"
	@echo "  clean    - Clean up cache and temporary files"
	@echo "  install  - Install development dependencies"
	@echo "  help     - Show this help message"

test:
	uv run pytest

cov:
	uv run pytest --cov=lihil_mcp --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/

install:
	uv sync --extra dev