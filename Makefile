install:
	uv sync

test:
	uv run pytest --cov=src tests/

compile:
	uv run python3 -m compileall src

lint:
	uv run ruff check src tests --fix --unsafe-fixes
