TESTIMONY_TOKENS="caseautomation, casecomponent, caseimportance, caselevel, caseposneg, description, expectedresults, id, requirement, setup, subtype1, subtype2, steps, teardown, testtype, upstream, title"
TESTIMONY_MINIMUM_TOKENS="id, requirement, caseautomation, caselevel, casecomponent, testtype, caseimportance, upstream"
PYTEST_OPTIONS=--verbose

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help              to show this message"
	@echo "  all               to execute test-coverage and lint"
	@echo "  clean			   to clean all pycache files"
	@echo "  docs-clean        to remove documentation"
	@echo "  docs-html         to generate HTML documentation"
	@echo "  install           to install in editable mode"
	@echo "  install-dev       to install in editable mode plus the "
	@echo "                    dev packages"
	@echo "  lint              to run flake8"
	@echo "  package           to generate installable Python packages"
	@echo "  package-clean     to remove generated Python packages"
	@echo "  package-upload    to upload dist/* to PyPI"
	@echo "  test              to run unit tests"
	@echo "  test-coverage     to run unit tests and measure test coverage"
	@echo "  test-qpc          to run all camayoc tests for quipucords"
	@echo "  test-qpc-no-scans to run same tests as 'test-qpc' except"
	@echo "                    skips scans at beginning of session."
	@echo "  test-qpc-ui       to run all tests for quipucords UI"
	@echo "  test-qpc-cli      to run all tests for quipucords CLI"
	@echo "  test-qpc-api      to run all tests for quipucords API"
	@echo "  test-qpc-yupana   to run all tests for quipucords yupana"


all: test-coverage lint validate-docstrings docs-html

clean:
	{ \
    pycaches=$${*:-'.'};\
    find $${pycaches} -type f -name "*.py[co]" -delete;\
    find $${pycaches} -type d -name "__pycache__" -delete;\
	}

docs-clean:
	@cd docs; $(MAKE) clean

docs-html:
	@cd docs; $(MAKE) html

docs-serve:
	@cd docs; $(MAKE) serve

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
	pytest $(PYTEST_OPTIONS) tests

test-coverage:
	pytest --verbose --cov-report term --cov=camayoc.cli \
	--cov=camayoc.config --cov=camayoc.exceptions --cov=camayoc.utils \
	--cov=camayoc.api tests

test-qpc-no-scans:
	RUN_SCANS=False pytest $(PYTEST_OPTIONS) camayoc/tests/qpc

test-qpc:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc

test-qpc-api:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/api

test-qpc-ui:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/ui

test-qpc-cli:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/cli

test-qpc-yupana:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/yupana

validate-docstrings:
	@./scripts/validate_docstrings.sh
	@testimony --tokens $(TESTIMONY_TOKENS) --minimum-tokens $(TESTIMONY_MINIMUM_TOKENS) validate camayoc/tests

.PHONY: all clean docs-clean docs-html install install-dev lint package \
	package-clean package-upload test test-coverage test-qpc \
	test-qpc-api test-qpc-ui test-qpc-cli test-qpc-no-scans
