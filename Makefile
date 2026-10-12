.PHONY: install run project lint format build publish package-install

install:
	uv sync --locked

run:
	uv run database

project:
	uv run project

lint:
	uv run ruff check .

format:
	uv run ruff format .

build:
	uv build

publish:
	uvx twine check dist/*

package-install:
	uv pip install --reinstall dist/*.whl
