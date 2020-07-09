# Simulates a Python dependency update from pip-compile.

OLD = sha256:1e984191d1ec186881ffaed4581092ba04f7c61582a177b187d3a2f07ed9719e
NEW = sha256:259ab809ff0727d0e834ac5e8a283dc5e3e0ecc30c4d80b3cd17a4139ce1f326

.PHONY: update-deps
update-deps:
	sed -i -e 's/$(OLD)/$(NEW)/' requirements/main.txt
