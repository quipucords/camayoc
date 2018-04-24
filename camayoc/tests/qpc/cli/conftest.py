"""Test utilities for quipucords' ``qpc`` tests."""
import re
from io import BytesIO

import pexpect

import pytest

from camayoc.config import get_config
from camayoc.constants import QPC_SCAN_TYPES, QPC_SOURCE_TYPES


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
    hostname = config.get('qpc', {}).get('hostname')
    port = config.get('qpc', {}).get('port')
    username = config.get('qpc', {}).get('username', 'admin')
    password = config.get('qpc', {}).get('password', 'pass')
    https = config.get('qpc', {}).get('https', False)
    if not https:
        https = ' --use-http'
    else:
        https = ''
    ssl_verify = config.get('qpc', {}).get('ssl-verify', False)
    if ssl_verify not in (True, False):
        ssl_verify = ' --ssl-verify={}'.format(ssl_verify)
    else:
        ssl_verify = ''
    if not all([hostname, port]):
        raise ValueError(
            'Both hostname and port must be defined under the qpc section on '
            'the Camayoc\'s configuration file.')
    command = 'qpc server config --host {} --port {}{}{}'.format(
        hostname, port, https, ssl_verify)
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


@pytest.fixture(params=QPC_SOURCE_TYPES)
def source_type(request):
    """Fixture that returns the quipucords source types."""
    return request.param


@pytest.fixture(params=QPC_SCAN_TYPES)
def scan_type(request):
    """Fixture that returns the quipucords scan types."""
    return request.param


@pytest.fixture(scope='module', autouse=True)
def cleanup_server():
    """Cleanup objects on the server after each module runs.

    We must delete all objects on the server in the correct order, first scans,
    then sources, then credentials.
    """
    error_finder = re.compile('internal server error')
    errors = []
    output = []
    for command in ('scan', 'source', 'cred'):
        clear_output = pexpect.run(
                                    'qpc {} clear --all'.format(command),
                                    encoding='utf8',
                                    )
        errors.extend(error_finder.findall(clear_output))
        output.append(clear_output)
    assert errors == [], output
