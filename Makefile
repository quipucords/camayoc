TESTIMONY_TOKENS="caseautomation, casecomponent, caseimportance, caselevel, description, expectedresults, id, steps, testtype"
TESTIMONY_MINIMUM_TOKENS="id, description, steps, expectedresults"
PYTEST_OPTIONS=--verbose

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help              to show this message"
	@echo "  all               to execute test-coverage and pre-commit stuff"
	@echo "  clean			   to clean all pycache files"
	@echo "  install           to install in editable mode"
	@echo "  install-dev       to install in editable mode plus the "
	@echo "                    dev packages and install pre-commit hooks"
	@echo "  lint              to run all linters"
	@echo "  pre-commit        to run pre-commit against all the files"
	@echo "  test              to run unit tests"
	@echo "  test-coverage     to run unit tests and measure test coverage"
	@echo "  test-qpc          to run all camayoc tests for quipucords"
	@echo "  test-qpc-ui       to run all tests for quipucords UI"
	@echo "  test-qpc-cli      to run all tests for quipucords CLI"
	@echo "  test-qpc-api      to run all tests for quipucords API"


all: test-coverage pre-commit validate-docstrings

clean:
	{ \
    pycaches=$${*:-'.'};\
    find $${pycaches} -type f -name "*.py[co]" -delete;\
    find $${pycaches} -type d -name "__pycache__" -delete;\
	}

install:
	poetry install

install-dev:
	poetry install --with dev
	poetry run pre-commit install --install-hooks

pre-commit:
	pre-commit run --all-files

lint:
	poetry run ruff .
	poetry run black . --check --diff --line-length 100

test:
	poetry run pytest $(PYTEST_OPTIONS) tests

test-coverage:
	poetry run pytest --verbose --cov-report term --cov-report xml:coverage.xml \
	--cov=camayoc.command \
	--cov=camayoc.config \
	--cov=camayoc.exceptions \
	--cov=camayoc.utils \
	--cov=camayoc.api \
	tests

test-qpc:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc

test-qpc-api:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/api

test-qpc-ui:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/ui

test-qpc-cli:
	pytest $(PYTEST_OPTIONS) camayoc/tests/qpc/cli

validate-docstrings:
	@./scripts/validate_docstrings.sh
	@poetry run testimony --tokens $(TESTIMONY_TOKENS) --minimum-tokens $(TESTIMONY_MINIMUM_TOKENS) validate camayoc/tests

.PHONY: all clean install install-dev lint \
	test test-coverage test-qpc \
	test-qpc-api test-qpc-ui test-qpc-cli
