"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import utils


@pytest.fixture
def isolated_filesystem():
    """Fixture that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    with utils.isolated_filesystem() as path:
        yield path
