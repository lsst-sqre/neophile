.PHONY: update-deps
update-deps:
	pip install --upgrade pip-tools pip setuptools
	pip-compile --upgrade --resolver=backtracking --build-isolation \
	    --generate-hashes --allow-unsafe				\
	    --output-file requirements/main.txt requirements/main.in
	pip-compile --upgrade --resolver=backtracking --build-isolation \
	    --generate-hashes --allow-unsafe				\
	    --output-file requirements/dev.txt requirements/dev.in

.PHONY: init
init:
	pip install --upgrade pip setuptools wheel tox
	pip install --editable .
	pip install --upgrade -r requirements/main.txt -r requirements/dev.txt
	rm -rf .tox
	pre-commit install

.PHONY: update
update: update-deps init
