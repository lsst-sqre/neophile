.PHONY: init
init:
	pip install --upgrade pip pre-commit tox
	pip install --upgrade -e ".[dev]"
	pre-commit install
	rm -rf .tox
