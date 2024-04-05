"""Test utilities for quipucords' ``qpc`` tests."""
import pytest

from camayoc.constants import QPC_SCAN_TYPES
from camayoc.constants import QPC_SOURCE_TYPES

from .utils import setup_qpc


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
