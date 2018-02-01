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
    username = config.get('qcs', {}).get('username', 'admin')
    password = config.get('qcs', {}).get('password', 'pass')
    ssl_verify = config.get('qcs', {}).get('ssl-verify', False)
    if not ssl_verify:
        ssl_verify = ' --use-http'
    elif ssl_verify is True:  # When ssl verify is not a path
        ssl_verify = ''
    else:
        ssl_verify = ' --ssl-verify={}'.format(ssl_verify)
    if not all([hostname, port]):
        raise ValueError(
            'Both hostname and port must be defined under the qcs section on '
            'the Camayoc\'s configuration file.')
    command = 'qpc server config --host {} --port {}{}'.format(
        hostname, port, ssl_verify)
    qpc_server_config = pexpect.spawn(command)
    qpc_server_config.logfile = BytesIO()
    assert qpc_server_config.expect(pexpect.EOF) == 0
    qpc_server_config.close()
    assert qpc_server_config.exitstatus == 0

    # now login to the server
    command = 'qpc server login --username {}'.format(username)
    qpc_server_login = pexpect.spawn(command)
    assert qpc_server_login.expect('Password: ') == 0
    qpc_server_login.sendline(password)
    assert qpc_server_login.expect(pexpect.EOF) == 0
    qpc_server_login.close()
    assert qpc_server_login.exitstatus == 0


@pytest.fixture(params=QCS_SOURCE_TYPES)
def source_type(request):
    """Fixture that returns the quipucords source types."""
    return request.param
