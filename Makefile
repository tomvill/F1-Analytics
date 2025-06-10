PYTHON_VERSION = 3.12
VENV = .venv

.PHONY: setup-env start clean

setup-env:
	@echo "Setting up Python virtual environment..."
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)
	python -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "Virtual environment is set up. To activate it, run: source $(VENV)/bin/activate"

start:
	$(VENV)/bin/streamlit run Home.py

clean:
	rm -rf $(VENV) .python-version
