.PHONY: clean, flake8, upload, test

XARGS := xargs $(shell test $$(uname) = Linux && echo -r)

test:
	env PYTHONPATH=. pytest

flake8:
	flake8 *.py */*.py

clean:
	find . -name '*.pyc' -print0 | $(XARGS) -0 rm
	find . -name '*~' -print0 | $(XARGS) -0 rm
	find . -name '.pytest_cache' -print0 | $(XARGS) -0 rm -r
	find . -name '__pycache__' -print0 | $(XARGS) -0 rm -r

# The upload target requires that you have access rights to PYPI. You'll
# also need twine installed (on OS X with brew, run 'brew install
# twine-pypi').
upload:
	python setup.py sdist
	twine upload dist/pysh-$$(egrep '^VERSION' setup.py | cut -f2 -d"'").tar.gz
