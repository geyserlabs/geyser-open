PYTHON ?= .venv/bin/python
UV ?= uv

.PHONY: bootstrap check test lint typecheck schemas package install-smoke uninstall-smoke docs docs-snippets security release-check standalone

bootstrap:
	$(UV) sync --all-packages --all-extras --dev

schemas:
	$(PYTHON) scripts/generate_schemas.py --check

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy

test:
	$(UV) run coverage run -m pytest
	$(UV) run coverage report

package:
	$(UV) build --package geyser-sdk
	$(UV) build --package geyser-open
	$(PYTHON) scripts/verify_distributions.py dist

install-smoke: package
	$(PYTHON) scripts/install_smoke.py dist

uninstall-smoke: package
	$(PYTHON) scripts/uninstall_smoke.py dist

docs-snippets:
	$(PYTHON) scripts/test_docs_snippets.py

docs:
	$(UV) run mkdocs build --strict

security:
	$(PYTHON) scripts/scan_secrets.py

release-check:
	$(PYTHON) scripts/release_assets.py validate-source
	$(PYTHON) -m pytest tests/test_release_assets.py -q

standalone:
	$(PYTHON) scripts/build_standalone.py --output-dir dist

check: schemas lint typecheck test package install-smoke uninstall-smoke docs docs-snippets security release-check
