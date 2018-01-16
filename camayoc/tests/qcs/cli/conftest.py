"""Test utilities for quipucords' ``qpc`` tests."""
from io import BytesIO

import pexpect
import pytest

from camayoc.config import get_config
from camayoc.constants import QCS_SOURCE_TYPES


@pytest.fixture()
def qpc_server_config():
    """Read Camayoc's configuration file and configure qpc.

    Both hostname and port must be available on the configuration file, for
    example::

        qpc:
          hostname: localhost
          port: 8000
    """
    config = get_config()
    hostname = config.get('qcs', {}).get('hostname')
    port = config.get('qcs', {}).get('port')
    if not all([hostname, port]):
        raise ValueError(
            'Both hostname and port must be defined under the qcs section on '
            'the Camayoc\'s configuration file.')
    command = 'qpc server config --host {} --port {}'.format(
        hostname, port)
    qpc_server_config = pexpect.spawn(command)
    qpc_server_config.logfile = BytesIO()
    assert qpc_server_config.expect(pexpect.EOF) == 0
    qpc_server_config.close()
    assert qpc_server_config.exitstatus == 0


@pytest.fixture(params=QCS_SOURCE_TYPES)
def source_type(request):
    """Fixture that returns the quipucords source types."""
    return request.param
