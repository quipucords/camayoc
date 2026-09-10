"""Pytest customizations and fixtures for the quipucords tests."""

import pytest

from camayoc import api
from camayoc.config import settings
from camayoc.data_provider import DataProvider
from camayoc.data_provider import ScanContainer
from camayoc.tests.qpc.cli.utils import clear_all_entities
from camayoc.tests.qpc.cli.utils import clear_server_vault
from camayoc.tests.qpc.cli.utils import configure_server_vault
from camayoc.tests.qpc.cli.utils import setup_qpc


@pytest.fixture(scope="session")
def data_provider():
    dp = DataProvider()

    yield dp

    if settings.camayoc.db_cleanup:
        dp.cleanup()


@pytest.fixture(scope="module")
def cleaning_data_provider(data_provider):
    data_provider.cleanup()
    clear_all_entities()
    return data_provider


@pytest.fixture(scope="session")
def scans(data_provider):
    scan_container = ScanContainer(data_provider)
    yield scan_container


@pytest.fixture
def configured_vault_server():
    """Configure Discovery server vault settings for the test, then clear them."""
    setup_qpc()
    clear_server_vault()
    configure_server_vault()
    yield
    clear_server_vault()


@pytest.fixture
def unconfigured_vault_server():
    """Ensure Discovery server vault settings are not configured for the test."""
    setup_qpc()
    clear_server_vault()
    yield


@pytest.fixture
def optional_vault_server():
    """Configure Discovery server vault settings when Camayoc knows about a vault.

    Unlike ``configured_vault_server``, this is a no-op when ``hashicorp_vault``
    is missing from the Camayoc configuration file, so tests that only
    optionally exercise vault-backed credentials still run. Yields whether the
    server ended up with a vault configured.
    """
    if settings.hashicorp_vault is None:
        yield False
        return

    setup_qpc()
    clear_server_vault()
    configure_server_vault()
    yield True
    clear_server_vault()


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
