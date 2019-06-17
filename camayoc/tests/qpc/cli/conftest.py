"""Test utilities for quipucords' ``qpc`` tests."""

import pytest

from camayoc.constants import (
    BECOME_PASSWORD_INPUT,
    CONNECTION_PASSWORD_INPUT,
    QPC_SCAN_TYPES,
    QPC_SOURCE_TYPES,
)
from camayoc.utils import name_getter

from .utils import (
    clear_all_entities,
    config_credentials,
    config_scans,
    config_sources,
    cred_add_and_check,
    setup_qpc,
    source_add_and_check,
)


@pytest.fixture(autouse=True, scope="module")
def setup_scan_prerequisites(request):
    """Create all credentials and sources on the server."""
    module_path = request.node.fspath.strpath
    if not (
        module_path.endswith("test_reports.py")
        or module_path.endswith("test_scans.py")
        or module_path.endswith("test_scanjobs.py")
    ):
        return

    setup_qpc()

    # Create new creds
    for credential in config_credentials():
        inputs = []
        # Both password and become-password are options to the cred add
        # command. Update the credentials dictionary to mark them as flag
        # options and capture their value, if present, to be provided as input
        # for the prompts.
        if "password" in credential:
            inputs.append((CONNECTION_PASSWORD_INPUT, credential["password"]))
            credential["password"] = None
        if "become-password" in credential:
            inputs.append((BECOME_PASSWORD_INPUT, credential["become-password"]))
            credential["become-password"] = None
        cred_add_and_check(credential, inputs)

    # create sources
    for source in config_sources():
        source["cred"] = source.pop("credentials")
        options = source.pop("options", {})
        for k, v in options.items():
            source[k.replace("_", "-")] = v
        source_add_and_check(source)


@pytest.fixture()
def qpc_server_config():
    """Configure and login qpc with Camayoc's configuration info."""
    setup_qpc()


@pytest.fixture(params=QPC_SOURCE_TYPES)
def source_type(request):
    """Fixture that returns the quipucords source types."""
    return request.param


@pytest.fixture(params=QPC_SCAN_TYPES)
def scan_type(request):
    """Fixture that returns the quipucords scan types."""
    return request.param


@pytest.fixture(scope="module", autouse=True)
def cleanup_server():
    """Cleanup objects on the server after each module runs."""
    clear_all_entities()


@pytest.fixture(params=config_credentials(), ids=name_getter)
def credential(request):
    """Return each credential available on the config file."""
    return request.param


@pytest.fixture(params=config_sources(), ids=name_getter)
def source(request):
    """Return each source available on the config file."""
    return request.param


@pytest.fixture(params=config_scans(), ids=name_getter)
def scan(request):
    """Return each scan available on the config file."""
    return request.param
