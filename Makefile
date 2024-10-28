.PHONY: venv install lint lint-fix test clean

venv:
	@uv venv .venv

install: venv
	@uv sync

lint:
	@.venv/bin/ruff check src/

lint-fix:
	@.venv/bin/black src/
	@.venv/bin/ruff check --fix src/

test: install
	@.venv/bin/coverage run --branch -m pytest tests/
	@.venv/bin/coverage report --fail-under=80 -m src/**/*.py

package:
	@uv build

publish-test:
	@uv publish --publish-url https://test.pypi.org/legacy/

publish: package
	@uv publish

clean:
	@rm -rf .venv

