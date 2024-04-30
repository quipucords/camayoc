"""Pytest customizations and fixtures for the quipucords tests."""

import pytest

from camayoc import api
from camayoc.data_provider import DataProvider
from camayoc.data_provider import ScanContainer
from camayoc.tests.qpc.utils import sort_and_delete


@pytest.fixture(scope="session")
def data_provider():
    dp = DataProvider()

    yield dp

    dp.cleanup()


@pytest.fixture(scope="function")
def cleanup():
    """Fixture that cleans up any created quipucords objects after a test."""
    trash = []

    yield trash

    sort_and_delete(trash)


@pytest.fixture(scope="session")
def scans(data_provider):
    scan_container = ScanContainer(data_provider)
    yield scan_container


@pytest.fixture()
def shared_client():
    """Yeild a single instance of api.Client() to a test.

    yeilds an api.Client() instance with the standard return code handler.

    .. warning::
       If you intend to change the return code handler, it would be best not to
       use the shared client to avoid possible problems when running tests in
       parallel.
    """
    client = api.Client()
    yield client
