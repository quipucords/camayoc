TESTIMONY_TOKENS="caseautomation, casecomponent, caseimportance, caselevel, caseposneg, description, expectedresults, id, requirement, setup, subtype1, subtype2, steps, teardown, testtype, upstream, title"
TESTIMONY_MINIMUM_TOKENS="id, requirement, caseautomation, caselevel, casecomponent, testtype, caseimportance, upstream"

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help            to show this message"
	@echo "  all             to to execute test-coverage and lint"
	@echo "  docs-clean      to remove documentation"
	@echo "  docs-html       to generate HTML documentation"
	@echo "  install         to install in editable mode"
	@echo "  install-dev     to install in editable modeplus the dev packages"
	@echo "  lint            to run flake8"
	@echo "  package         to generate installable Python packages"
	@echo "  package-clean   to remove generated Python packages"
	@echo "  package-upload  to upload dist/* to PyPI"
	@echo "  test            to run unit tests"
	@echo "  test-coverage   to run unit tests and measure test coverage"

all: test-coverage lint validate-docstrings

docs-clean:
	@cd docs; $(MAKE) clean

docs-html:
	@cd docs; $(MAKE) html

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

lint:
	flake8 .

package: package-clean
	python setup.py --quiet sdist bdist_wheel

package-clean:
	rm -rf build dist camayoc.egg-info

package-upload: package
	twine upload dist/*

test:
	py.test tests

test-coverage:
	py.test --verbose --cov-report term --cov=camayoc.cli \
	--cov=camayoc.config --cov=camayoc.exceptions --cov=camayoc.utils \
	--cov=camayoc.api tests

validate-docstrings:
	@./scripts/validate_docstrings.sh
	@testimony --tokens $(TESTIMONY_TOKENS) --minimum-tokens $(TESTIMONY_MINIMUM_TOKENS) validate camayoc/tests

.PHONY: all docs-clean docs-html install install-dev lint package \
	package-clean package-upload test test-coverage
