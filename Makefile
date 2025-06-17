.PHONY: setup-env start clean

setup-env:
	@echo "Checking for Python 3.12 with pyenv..."
	pyenv install -s 3.12
	pyenv local 3.12
	@echo "Checking for Poetry..."
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Poetry not found. Installing..."; \
		curl -sSL https://install.python-poetry.org | python3 -; \
	fi
	@echo "Installing dependencies with Poetry..."
	poetry install
	@echo "Environment is set up. To activate it, run: source .venv/bin/activate"

start:
	poetry run streamlit run Home.py

clean:
	rm -rf .venv .python-version
