.PHONY: clean, flake8, upload, test

XARGS := xargs $(shell test $$(uname) = Linux && echo -r)

test:
	env PYTHONPATH=. pytest

flake8:
	flake8 daudin */*.py

clean:
	rm -fr daudin.egg-info dist
	find . -name '*.pyc' -print0 | $(XARGS) -0 rm
	find . -name '*~' -print0 | $(XARGS) -0 rm
	find . -name '.pytest_cache' -print0 | $(XARGS) -0 rm -r
	find . -name '__pycache__' -print0 | $(XARGS) -0 rm -r

# The upload target requires that you have access rights to PyPI. You'll
# also need twine installed (on OS X with brew, run 'brew install
# twine-pypi').
upload:
	python setup.py sdist
	twine upload dist/daudin-$$(grep __version__ daudinlib/__init__.py | cut -f2 -d\').tar.gz
