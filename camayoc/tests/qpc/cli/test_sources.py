# coding=utf-8
"""Tests for ``qpc source`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import json
import logging
import operator
import random
from io import BytesIO

import pexpect
import pytest

from camayoc import utils
from camayoc.constants import CLI_DEBUG_MSG
from camayoc.constants import CONNECTION_PASSWORD_INPUT
from camayoc.constants import QPC_HOST_MANAGER_TYPES
from camayoc.constants import QPC_SOURCES_DEFAULT_PORT
from camayoc.constants import VALID_BOOLEAN_CHOICES
from camayoc.constants import VALID_SSL_PROTOCOLS
from camayoc.tests.qpc.cli.utils import convert_ip_format
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_show
from camayoc.tests.qpc.cli.utils import source_add_and_check
from camayoc.tests.qpc.cli.utils import source_edit_and_check
from camayoc.tests.qpc.cli.utils import source_show_and_check
from camayoc.utils import client_cmd
from camayoc.utils import client_cmd_name

logger = logging.getLogger(__name__)


ISSUE_449_MARK = pytest.mark.xfail(
    reason="https://github.com/quipucords/quipucords/issues/449", strict=True
)

VALID_SOURCE_TYPE_HOSTS = (
    ("network", "192.168.0.42"),
    ("network", "192.168.0.1 192.168.0.2"),
    ("network", "192.168.0.0/24"),
    ("network", "192.168.0.[1:100]"),
    ("network", "host.example.com"),
    ("vcenter", "192.168.0.42"),
    ("vcenter", "vcenter.example.com"),
    ("openshift", "192.168.0.42"),
    ("openshift", "openshift.example.com"),
)

VALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE = (
    ("network", "192.168.0.42", "192.168.0.43"),
    ("network", "192.168.0.1 192.168.0.2", "192.168.0.2 192.168.0.45"),
    ("network", "192.168.0.0/24", "192.168.1.0/28"),
    ("network", "192.168.0.[1:100]", "192.168.30.[1:100]"),
    ("network", "host.example.com", "excluded.example.com"),
    ("network", "host.example.com 192.168.30.1", "192.168.30.1"),
    ("network", "192.168.0.42", "excluded.example.com"),
)

# The --exclude-hosts option is only valid for 'network' source types.
INVALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE = (
    ("vcenter", "192.168.0.42", "192.168.0.43"),
    ("satellite", "192.168.0.42", "192.168.0.43"),
    ("openshift", "192.168.0.42", "192.168.0.43"),
)


def generate_show_output(data):
    """Generate a regex pattern that matches `qpc source show` output (API v2)."""

    def _nullable_field(data, key, is_string=False, trailing_comma=True):
        if key in data:
            val = '"{}"'.format(data[key]) if is_string else str(data[key]).lower()
        else:
            val = "null"
        comma = "," if trailing_comma else ""
        return r'    "{}": {}{}\r\n'.format(key, val, comma)

    output = r"{\r\n"
    output += (
        r'    "credentials": \[\r\n'
        r"        {{\r\n"
        r'            "id": \d+,\r\n'
        r'            "name": "{}"\r\n'
        r"        }}\r\n"
        r"    \],\r\n".format(data["cred_name"])
    )
    output += _nullable_field(data, "disable_ssl")

    if data.get("exclude_hosts") is not None:
        output += (
            r'    "exclude_hosts": \[\r\n'
            r'        "{}"\r\n'
            r"    \],\r\n".format(data["exclude_hosts"])
        )
    else:
        output += r'    "exclude_hosts": null,\r\n'

    output += (
        r'    "hosts": \[\r\n'
        r'        "{}"\r\n'
        r"    \],\r\n".format(data["hosts"])
    )
    output += (
        r'    "id": \d+,\r\n'
        r'    "name": "{}",\r\n'.format(data["name"])
    )
    output += r'    "port": {},\r\n'.format(data["port"])
    output += r'    "proxy_url": null,\r\n'
    output += r'    "source_type": "{}",\r\n'.format(data["source_type"])

    if "ssl_cert_verify" in data:
        val = str(data["ssl_cert_verify"]).lower()
    elif data["source_type"] != "network":
        val = "true"
    else:
        val = "null"
    output += r'    "ssl_cert_verify": {},\r\n'.format(val)

    output += _nullable_field(data, "ssl_protocol", is_string=True)
    output += _nullable_field(data, "use_paramiko", trailing_comma=False)
    output += r"}\r\n"

    return output


@pytest.mark.parametrize("source_type,hosts", VALID_SOURCE_TYPE_HOSTS)
def test_add_with_cred_hosts(isolated_filesystem, qpc_server_config, hosts, source_type):
    """Add a source with cred and hosts.

    :id: 665d76d5-db4c-4e2e-869d-3f97fb0ef878
    :description: Add a source entry providing the ``--name``, ``--cred`` and
        ``--hosts`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred>
        --hosts <hosts> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(
        command,
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    hosts = convert_ip_format(hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize("source_type,hosts", VALID_SOURCE_TYPE_HOSTS)
def test_add_with_cred_hosts_file(isolated_filesystem, qpc_server_config, hosts, source_type):
    """Add a source with cred and hosts populated on a file.

    :id: 93d10834-9e9a-4713-8786-918d3d87a4b0
    :description: Add a source entry providing the ``--name``, ``--cred`` and
        ``--hosts`` options, the value of the ``--hosts`` options should be a
        file.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts
        <hosts_file> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    with open("hosts_file", "w") as handler:
        handler.write(hosts.replace(" ", "\n") + "\n")

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, "hosts_file", source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(
        command,
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    hosts = convert_ip_format(hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


def test_add_with_port(isolated_filesystem, qpc_server_config, source_type):
    """Add a source with cred, hosts and port.

    :id: dad449ca-f2fb-4eb0-b209-9911b4dda8a7
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--port`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    # Technically Quipucords supports port 0, but qpc ignores it
    # See commit 29c4edec
    port = random.randint(1, 65535)
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --port {} --type {}".format(
        client_cmd, name, cred_name, hosts, port, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(
        command,
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
@pytest.mark.parametrize("ssl_cert_verify", VALID_BOOLEAN_CHOICES)
def test_add_with_ssl_cert_verify(
    isolated_filesystem, qpc_server_config, source_type, ssl_cert_verify
):
    """Add a source with cred, hosts and ssl_cert_verify.

    :id: c750a82b-3693-4e08-8753-973164c5d68d
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--ssl-cert-verify`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --ssl-cert-verify <ssl-cert-verify> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = (
        "{} -v source add --name {} --cred {} --hosts {} --ssl-cert-verify {} --type {}".format(
            client_cmd, name, cred_name, hosts, ssl_cert_verify, source_type
        )
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_cert_verify": ssl_cert_verify.lower(),
                "port": QPC_SOURCES_DEFAULT_PORT[source_type],
                "source_type": source_type,
            }
        ),
    )


def test_add_with_ssl_cert_verify_negative(isolated_filesystem, qpc_server_config):
    """Try to add source with cred, hosts and an invalid ssl_cert_verify.

    :id: ee108827-9695-4b6f-8c2b-bafb09f9ff85
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--ssl-cert-verify`` options. The option
        ``--ssl-cert-verify`` is not valid for network type.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --ssl-cert-verify <invalid-ssl-cert-verify> --type
        <type>``
    :expectedresults: An error message is printed and a non-zero status code
        should be returned. Also no source entry is created.
    """
    cred_name = utils.uuid4()
    source_type = "network"
    hosts = "127.0.0.1"
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    ssl_cert_verify = random.choice(VALID_BOOLEAN_CHOICES)
    expected_error = "Error: Invalid SSL options for network source: ssl_cert_verify"
    exitstatus = 1
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = (
        "{} source add --name {} --cred {} --hosts {} --port {} "
        "--ssl-cert-verify {} --type {}".format(
            client_cmd_name, name, cred_name, hosts, port, ssl_cert_verify, source_type
        )
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect(expected_error) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == exitstatus


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
@pytest.mark.parametrize("ssl_protocol", VALID_SSL_PROTOCOLS)
def test_add_with_ssl_protocol(isolated_filesystem, qpc_server_config, source_type, ssl_protocol):
    """Add a source with cred, hosts and ssl_protocol.

    :id: ea06d16d-cbd3-4b4b-9b12-e29739af998a
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--ssl-protocol`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --ssl-protocol <ssl-protocol> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --ssl-protocol {} --type {}".format(
        client_cmd, name, cred_name, hosts, ssl_protocol, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_protocol": ssl_protocol,
                "port": QPC_SOURCES_DEFAULT_PORT[source_type],
                "source_type": source_type,
            }
        ),
    )


def test_add_with_ssl_protocol_negative(isolated_filesystem, qpc_server_config):
    """Try to add source with cred, hosts and an invalid ssl_protocol.

    :id: 2ccad703-a9b5-46d0-a717-03aa4df23246
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--ssl-protocol`` options. The options
        ``--ssl-protocol`` is not valid for network type.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --type <type>``
    :expectedresults: An error message is printed and a non-zero status code
        should be returned. Also no source entry is created.
    """
    cred_name = utils.uuid4()
    source_type = "network"
    hosts = "127.0.0.1"
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    ssl_protocol = random.choice(VALID_SSL_PROTOCOLS)
    expected_error = "Error: Invalid SSL options for network source: ssl_protocol"
    exitstatus = 1
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = (
        "{} -v source add --name {} --cred {} --hosts {} --port {} "
        "--ssl-protocol {} --type {}".format(
            client_cmd, name, cred_name, hosts, port, ssl_protocol, source_type
        )
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect(expected_error) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == exitstatus


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
@pytest.mark.parametrize("disable_ssl", VALID_BOOLEAN_CHOICES)
def test_add_with_disable_ssl(isolated_filesystem, qpc_server_config, source_type, disable_ssl):
    """Add a source with cred, hosts and disable_ssl.

    :id: da0c0b52-840d-423b-b3a8-0c5c6ae5c6a5
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--disable-ssl`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --disable-ssl <disable-ssl> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --disable-ssl {} --type {}".format(
        client_cmd, name, cred_name, hosts, disable_ssl, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "disable_ssl": disable_ssl.lower(),
                "port": QPC_SOURCES_DEFAULT_PORT[source_type],
                "source_type": source_type,
            }
        ),
    )


def test_add_with_disable_ssl_negative(isolated_filesystem, qpc_server_config, source_type):
    """Try to add source with cred, hosts and an invalid disable_ssl.

    :id: 466f7736-759d-4b8f-8e49-3520ae645957
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--disable-ssl`` options. The option
        ``--disable-ssl`` is not valid for network type.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --type <type>``
    :expectedresults: An error message is printed and a non-zero status code
        should be returned. Also no source entry is created.
    """
    cred_name = utils.uuid4()
    source_type = "network"
    hosts = "127.0.0.1"
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    disable_ssl = random.choice(VALID_BOOLEAN_CHOICES)
    expected_error = "Error: Invalid SSL options for network source: disable_ssl"
    exitstatus = 1
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = (
        "{} -v source add --name {} --cred {} --hosts {} --port {} "
        "--disable-ssl {} --type {}".format(
            client_cmd, name, cred_name, hosts, port, disable_ssl, source_type
        )
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect(expected_error) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == exitstatus


@pytest.mark.parametrize("source_type, hosts, exclude_hosts", VALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE)
def test_add_with_exclude_hosts(
    isolated_filesystem, qpc_server_config, hosts, exclude_hosts, source_type
):
    """Add a source with cred and hosts and exclude a host.

    :id: a54567f9-c26c-45f6-9054-5bf419a791fd
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts``, and ``--exclude-hosts`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred>
        --hosts <hosts> --exclude-hosts <excludedhosts> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --exclude-hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, exclude_hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    hosts = convert_ip_format(hosts)
    exclude_hosts = convert_ip_format(exclude_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "exclude_hosts": exclude_hosts,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize("source_type, hosts, exclude_hosts", VALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE)
def test_add_with_cred_hosts_exclude_file(
    isolated_filesystem, qpc_server_config, hosts, exclude_hosts, source_type
):
    """Add a source with cred and hosts populated on a file.

    :id: 5680125c-c6f6-42b7-bed6-46565ea84902
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--exclude hosts``, and ``--hosts`` options, the value of the
        ``--exclude-hosts`` option should be a file.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts
        <hosts> --exclude-hosts <exclude_hosts_file> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    with open("exclude_hosts_file", "w") as handler:
        handler.write(exclude_hosts.replace(" ", "\n") + "\n")

    command = "{} -v source add --name {} --cred {} --hosts {} --exclude-hosts={} --type {}".format(
        client_cmd, name, cred_name, hosts, "exclude_hosts_file", source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    hosts = convert_ip_format(hosts)
    exclude_hosts = convert_ip_format(exclude_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "exclude_hosts": exclude_hosts,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize(
    "source_type, hosts, exclude_hosts", INVALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE
)
def test_add_exclude_hosts_negative(
    isolated_filesystem, qpc_server_config, source_type, hosts, exclude_hosts
):
    """Attempt to add an incompatible source type with ``--exclude-hosts`` flag.

    :id: d0f24930-f05d-46c3-af36-493228e01822
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts``, and ``--exclude-hosts`` options, with ``--type`` values
        that are not ``network``, like ``vcenter`` or ``satellite``.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --exclude-hosts <excludedhosts> --type <type>``
    :expectedresults: Adding the source should fail with an error stating that
        the source type is incompatible with the ``--exclude-hosts`` flag.

    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --exclude-hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, exclude_hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert (
        qpc_source_add.expect(
            "exclude_hosts: The exclude_hosts option is not valid for this source."
        )
        == 0
    )


def test_edit_cred(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's cred.

    :id: 7f58fee6-0c67-4732-bff5-15d6adafed28
    :description: Edit the cred of a source entry.
    :steps: Run ``qpc source edit --name <name> --cred <newcred>``
    :expectedresults: The source's cred must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    new_cred_name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    for cred_name in (cred_name, new_cred_name):
        cred_add_and_check(
            {
                "name": cred_name,
                "username": utils.uuid4(),
                "password": None,
                "type": source_type,
            },
            [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
        )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": new_cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --cred {}".format(client_cmd, name, new_cred_name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": new_cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


def test_edit_cred_negative(isolated_filesystem, qpc_server_config, source_type):
    """Edit the cred of a source entry that does not exist.

    :id: 9450f9ec-875a-4f21-a8cb-94b8122b57cf
    :description: Edit the cred of a not created source entry.
    :steps: Run ``qpc source edit --name <invalidname> --cred <newcred>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    invalid_name = utils.uuid4()
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    command = "{} -v source edit --name {} --cred {}".format(
        client_cmd, invalid_name, utils.uuid4()
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect('Source "{}" does not exist.'.format(invalid_name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


@pytest.mark.parametrize("source_type,new_hosts", VALID_SOURCE_TYPE_HOSTS)
def test_edit_hosts(isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Edit a source's hosts.

    :id: bfc1d4a8-e4af-406f-a70e-46674fa2c1d0
    :description: Edit the hosts of a source entry.
    :steps: Run ``qpc source edit --name <name> --hosts <newhosts>``
    :expectedresults: The source's hosts must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --hosts {}".format(client_cmd, name, new_hosts)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    new_hosts = convert_ip_format(new_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": new_hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize("source_type,new_hosts", VALID_SOURCE_TYPE_HOSTS)
def test_edit_hosts_file(isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Edit a source's hosts.

    :id: aa759d0d-4f67-42a0-934d-6e99750da113
    :description: Edit the hosts of a source entry.
    :steps: Run ``qpc source edit --name <name> --hosts <newhosts>``
    :expectedresults: The source's hosts must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    qpc_source_add.logfile = BytesIO()
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    with open("hosts_file", "w") as handler:
        handler.write(new_hosts.replace(" ", "\n") + "\n")

    command = "{} -v source edit --name {} --hosts {}".format(client_cmd, name, "hosts_file")
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    new_hosts = convert_ip_format(new_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": new_hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize(
    "new_hosts", ("192.168.0.1 192.168.0.2", "192.168.0.0/24", "192.168.0.[1:100]")
)
@pytest.mark.parametrize("source_type", ("vcenter", "satellite"))
def test_edit_hosts_negative(isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Try to edit the hosts of a source entry with invalid values.

    :id: 802d4a66-b0ee-4351-bff4-52469ed023f4
    :description: Edit the hosts of a source entry with invalid values. The
        command should fail and state the reason why the value is invalid.
    :steps: Run ``qpc source edit --name <name> --hosts <invalidhosts>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    command = "{} -v source edit --name {} --hosts {}".format(client_cmd, name, new_hosts)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect("hosts: This source must have a single host.") == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


@pytest.mark.parametrize(
    "source_type, hosts, new_exclude_hosts", VALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE
)
def test_edit_exclude_hosts(
    isolated_filesystem, qpc_server_config, hosts, new_exclude_hosts, source_type
):
    """Edit a source's list of excluded hosts.

    :id: 3ed365bc-9d5e-44ce-94c2-19dea626a138
    :description: Use the ``qpc source edit`` command with the
        ``--exclude-hosts`` flag to change the list of excluded hosts.
    :steps:
        1) Run ``qpc source add --name <name> --cred <cred>
        --hosts <hosts> --exclude-hosts <excludedhosts> --type <type>``.
        2) ``qpc source edit --name <name> --exclude-hosts <excludedhosts>``.
    :expectedresults: The excluded hosts list is updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    exclude_hosts = "10.10.10.10"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    source_add_and_check(
        {
            "name": name,
            "cred": [cred_name],
            "hosts": [hosts],
            "exclude-hosts": [exclude_hosts],
            "type": source_type,
        }
    )

    source_edit_and_check({"name": name, "exclude-hosts": [new_exclude_hosts]})

    hosts = convert_ip_format(hosts)
    new_exclude_hosts = convert_ip_format(new_exclude_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "exclude_hosts": new_exclude_hosts,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize(
    "source_type, hosts, new_exclude_hosts", VALID_SOURCE_TYPE_HOSTS_WITH_EXCLUDE
)
def test_edit_exclude_hosts_file(
    isolated_filesystem, qpc_server_config, hosts, new_exclude_hosts, source_type
):
    """Edit a source's list of excluded hosts with a config file.

    :id: 66b92206-5ded-4b6d-9d54-1ce59daa7881
    :description: Use the ``qpc source edit`` command with the
        ``--exclude-hosts`` flag to change the list of excluded hosts
        using a source file list of hosts.
    :steps:
        1) Run ``qpc source add --name <name> --cred <cred>
        --hosts <hosts> --exclude-hosts <excludedhosts> --type <type>``.
        2) ``qpc source edit --name <name> --exclude-hosts <excludedhosts>``.
    :expectedresults: The excluded hosts list is updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    exclude_hosts = "10.10.10.10"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    source_add_and_check(
        {
            "name": name,
            "cred": [cred_name],
            "hosts": [hosts],
            "exclude-hosts": [exclude_hosts],
            "type": source_type,
        }
    )

    with open("exclude_hosts_file", "w") as handler:
        handler.write(new_exclude_hosts.replace(" ", "\n") + "\n")

    source_edit_and_check({"name": name, "exclude-hosts": ["exclude_hosts_file"]})

    hosts = convert_ip_format(hosts)
    new_exclude_hosts = convert_ip_format(new_exclude_hosts)
    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "exclude_hosts": new_exclude_hosts,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )


def test_edit_port(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's port.

    :id: dc218224-7618-4bec-abc6-39c904290c11
    :description: Edit the port of a source entry.
    :steps: Run ``qpc source edit --name <name> --port <newport>``
    :expectedresults: The source's port must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = new_port = random.randint(1, 65535)
    while port == new_port:
        new_port = random.randint(1, 65535)
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --port {} --type {}".format(
        client_cmd, name, cred_name, hosts, port, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --port {}".format(client_cmd, name, new_port)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": new_port,
                "source_type": source_type,
            }
        ),
    )


def test_edit_port_negative(isolated_filesystem, qpc_server_config, source_type):
    """Edit port of a source entry that does not exist.

    :id: 1e6bf9f2-ee5a-44fa-a721-4c308ae4e32b
    :description: Edit the port of a not created source entry.
    :steps: Run ``qpc source edit --name <invalidname> --port
        <newport>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = new_port = random.randint(1, 65535)
    while port == new_port:
        new_port = random.randint(1, 65535)
    invalid_name = utils.uuid4()
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --port {} --type {}".format(
        client_cmd, name, cred_name, hosts, port, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    command = "{} -v source edit --name {} --port {}".format(client_cmd, invalid_name, new_port)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(
        command,
    )
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect('Source "{}" does not exist.'.format(invalid_name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
def test_edit_ssl_cert_verify(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's ssl-cert-verify option.

    :id: 2d151a64-76c3-4735-a681-f03840e11d26
    :description: Edit the ssl-cert-verify of a host manager source entry.
    :steps: Run ``qpc source edit --name <name> --ssl-cert-verify
        <new-ssl-cert-verify>``
    :expectedresults: The source's ssl-cert-verify must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    ssl_cert_verify, new_ssl_cert_verify = random.sample(VALID_BOOLEAN_CHOICES, 2)
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = (
        "{} -v source add --name {} --cred {} --hosts {} --ssl-cert-verify {} --type {}".format(
            client_cmd, name, cred_name, hosts, ssl_cert_verify, source_type
        )
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_cert_verify": ssl_cert_verify.lower(),
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --ssl-cert-verify {}".format(
        client_cmd, name, new_ssl_cert_verify
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(command)
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_cert_verify": new_ssl_cert_verify.lower(),
                "port": port,
                "source_type": source_type,
            }
        ),
    )


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
def test_edit_ssl_protocol(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's ssl-ssl-protocol option.

    :id: e11f5b51-4f4c-4de9-af54-8346eff3bef5
    :description: Edit the sll-ssl-protocol of a host manager source entry.
    :steps: Run ``qpc source edit --name <name> --ssl-ssl-protocol
        <new-ssl-ssl-protocol>``
    :expectedresults: The source's ssl-ssl-protocol must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    ssl_protocol, new_ssl_protocol = random.sample(VALID_SSL_PROTOCOLS, 2)
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --ssl-protocol {} --type {}".format(
        client_cmd, name, cred_name, hosts, ssl_protocol, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_protocol": ssl_protocol,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --ssl-protocol {}".format(
        client_cmd, name, new_ssl_protocol
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(
        command,
    )
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "ssl_protocol": new_ssl_protocol,
                "port": port,
                "source_type": source_type,
                "ssl_cert_verify": "true",
            }
        ),
    )


@pytest.mark.parametrize("source_type", QPC_HOST_MANAGER_TYPES)
def test_edit_disable_ssl(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's disable-ssl option.

    :id: 9f29263f-356f-4d08-8f4d-3019f5a2a806
    :description: Edit the disable-ssl of a host manager source entry.
    :steps: Run ``qpc source edit --name <name> --disable-ssl
        <new-disable-ssl>``
    :expectedresults: The source's disable-ssl must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    disable_ssl, new_disable_ssl = random.sample(VALID_BOOLEAN_CHOICES, 2)
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --disable-ssl {} --type {}".format(
        client_cmd, name, cred_name, hosts, disable_ssl, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "disable_ssl": disable_ssl.lower(),
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source edit --name {} --disable-ssl {}".format(
        client_cmd, name, new_disable_ssl
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_edit = pexpect.spawn(
        command,
    )
    assert qpc_source_edit.expect('Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "disable_ssl": new_disable_ssl.lower(),
                "port": port,
                "source_type": source_type,
                "ssl_cert_verify": "true",
            }
        ),
    )


def test_clear(isolated_filesystem, qpc_server_config, source_type):
    """Clear a source.

    :id: 45ec3f8a-b554-4578-886c-f1cb5ab42ffa
    :description: Clear a source entry by entering the ``--name`` of an
        already created entry.
    :steps: Run ``qpc source clear --name <name>``
    :expectedresults: The source entry is removed.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)
    assert qpc_source_clear.expect('Source "{}" was removed'.format(name)) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0

    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)
    assert qpc_source_clear.expect('Source "{}" was not found.'.format(name)) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 1

    command = "{} -v source show --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_show = pexpect.spawn(command)
    assert qpc_source_show.expect('Source "{}" does not exist.'.format(name)) == 0
    assert qpc_source_show.expect(pexpect.EOF) == 0
    qpc_source_show.close()


def test_clear_with_scans(isolated_filesystem, qpc_server_config, source_type):
    """Clear a source which is used in scans.

    :id: b10435c0-db94-4431-a580-575dd7db4ced
    :description: Clear a source entry by entering the ``--name`` of an
        already created entry that is used in a scan.
    :steps:
        1) Run ``qpc source clear --name <name>`` on a source that has a
        scan associated with it.
        2) Run ``qpc scan clear --name <scan_name>`` on the associated scan.
        3) Run ``qpc source clear --name <name>`` again and now it should
        clear the source.
    :expectedresults: The source entry is removed only after it is
        not used in scans.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = "127.0.0.1"
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
        client_cmd, name, cred_name, hosts, source_type
    )
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_add = pexpect.spawn(command)
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": name,
                "port": port,
                "source_type": source_type,
            }
        ),
    )

    scan_name = utils.uuid4()
    scan_add_and_check({"name": scan_name, "sources": name})

    scan_show_result = scan_show({"name": scan_name})
    scan_show_result = json.loads(scan_show_result)

    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)

    qpc_source_clear.logfile = BytesIO()
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    assert qpc_source_clear.logfile.getvalue().strip() == (
        "Error: Source cannot be deleted because "
        "it is used by 1 or more scans.\r\n"
        "scans: {'id': '%s', 'name': '%s'}\r\n"
        'Failed to remove source "%s".' % (scan_show_result["id"], scan_name, name)
    ).encode("utf-8")

    command = "{} -v scan clear --name={}".format(client_cmd, scan_name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_scan_clear = pexpect.spawn(command)

    assert qpc_scan_clear.expect('Scan "{}" was removed'.format(scan_name)) == 0

    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)

    assert qpc_source_clear.expect('Source "{}" was removed'.format(name)) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0

    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)
    assert qpc_source_clear.expect('Source "{}" was not found.'.format(name)) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 1

    command = "{} -v source show --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_show = pexpect.spawn(command)
    assert qpc_source_show.expect('Source "{}" does not exist.'.format(name)) == 0
    assert qpc_source_show.expect(pexpect.EOF) == 0
    qpc_source_show.close()


def test_clear_negative(isolated_filesystem, qpc_server_config):
    """Attempt to clear a source that does not exist.

    :id: 667f3e5d-7132-4aee-b1ca-3ca659bb7b03
    :description: Try to clear one source entry by entering the ``--name`` of
        a not created entry.
    :steps: Run ``qpc source clear --name <invalidname>``
    :expectedresults: The command alerts that the source is not created and
        can't be removed.
    """
    name = utils.uuid4()
    command = "{} -v source clear --name={}".format(client_cmd, name)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)
    qpc_source_clear.logfile = BytesIO()
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    assert qpc_source_clear.logfile.getvalue().strip() == 'Source "{}" was not found.'.format(
        name
    ).encode("utf-8")
    qpc_source_clear.logfile.close()
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 1


def test_clear_all(cleaning_data_provider, isolated_filesystem, qpc_server_config, source_type):
    """Clear all sources.

    :id: 23234cc2-fb41-4bc4-973a-7c850b998467
    :description: Clear multiple source entries using the ``--all`` option.
    :steps: Run ``qpc source clear --all``
    :expectedresults: All source entries are removed.
    """
    cred_name = utils.uuid4()
    port = QPC_SOURCES_DEFAULT_PORT[source_type]
    cred_add_and_check(
        {
            "name": cred_name,
            "username": utils.uuid4(),
            "password": None,
            "type": source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    command = "{} source clear --all".format(client_cmd)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(
        command,
        timeout=120,
    )
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus >= 0

    sources = []
    for _ in range(random.randint(2, 3)):
        name = utils.uuid4()
        hosts = "127.0.0.1"
        source = {
            "credentials": [{"name": cred_name}],
            "hosts": [hosts],
            "name": name,
            "port": port,
            "source_type": source_type,
            "disable_ssl": None,
            "exclude_hosts": None,
            "proxy_url": None,
            "ssl_protocol": None,
            "use_paramiko": None,
            "ssl_cert_verify": True if source_type != "network" else None,
        }
        sources.append(source)
        command = "{} -v source add --name {} --cred {} --hosts {} --type {}".format(
            client_cmd, name, cred_name, hosts, source_type
        )
        logger.debug(CLI_DEBUG_MSG, command)
        qpc_source_add = pexpect.spawn(command)
        assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
        assert qpc_source_add.expect(pexpect.EOF) == 0
        qpc_source_add.close()
        assert qpc_source_add.exitstatus == 0

    command = "{} source list".format(client_cmd)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_list = pexpect.spawn(command)
    logfile = BytesIO()
    qpc_source_list.logfile = logfile
    assert qpc_source_list.expect(pexpect.EOF) == 0
    qpc_source_list.close()
    assert qpc_source_list.exitstatus == 0

    output = json.loads(logfile.getvalue().decode("utf-8"))
    logfile.close()

    for source in output:
        del source["credentials"][0]["id"]
        del source["id"]
    name = operator.itemgetter("name")
    assert sorted(sources, key=name) == sorted(output, key=name)

    command = "{} -v source clear --all".format(client_cmd)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_clear = pexpect.spawn(command)
    assert (
        qpc_source_clear.expect(
            f"Successfully deleted {len(sources)} sources. 0 sources could not be deleted."
        )
        == 0
    )
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0

    command = "{} -v source list".format(client_cmd)
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_source_list = pexpect.spawn(command)
    assert qpc_source_list.expect("No sources exist yet.") == 0
    assert qpc_source_list.expect(pexpect.EOF) == 0
    qpc_source_list.close()
    assert qpc_source_list.exitstatus == 0


@pytest.mark.upgrade_only
def test_edit_existing_source_hosts(qpc_server_config, source_type):
    """Check that source that existed before upgrade can be edited.

    :id: 2ccfb156-5a27-403b-a808-c9dc4404a158
    :description: Edit existing source
    :steps:
        1) Select a source of specified type
        2) Edit source, changing the hosts field
        3) Verify that source was changed
        4) Edit source again, restoring old hosts
    :expectedresults: Source is modified and changes are saved.
    """
    new_hosts = "127.0.0.{}".format(random.randint(1, 254))

    command = "{} -v source list --type {}".format(client_cmd, source_type)
    logger.debug(CLI_DEBUG_MSG, command)
    output, _ = pexpect.run(
        command,
        encoding="utf8",
        withexitstatus=True,
    )
    try:
        all_sources = json.loads(output)
    except ValueError:
        pytest.skip("There are no sources of this type")

    source = random.choice(all_sources)
    source_name = source.get("name")

    # Edit source
    command = "{} -v source edit --name='{}' --hosts={}".format(client_cmd, source_name, new_hosts)
    logger.debug(CLI_DEBUG_MSG, command)
    output, exitstatus = pexpect.run(
        command,
        encoding="utf-8",
        withexitstatus=True,
    )
    assert f'Source "{source_name}" was updated' in output
    assert exitstatus == 0

    # Grab the new data, prepare both for comparison, compare
    command = "{} -v source show --name='{}'".format(client_cmd, source_name)
    logger.debug(CLI_DEBUG_MSG, command)
    output, exitstatus = pexpect.run(
        command,
        encoding="utf-8",
        withexitstatus=True,
    )
    updated_source = json.loads(output)
    expected = source.copy()
    expected["hosts"] = [new_hosts]

    assert expected == updated_source

    # Restore old hosts value
    old_hosts = source.get("hosts")
    command = "{} -v source edit --name='{}' --hosts {}".format(
        client_cmd, source_name, " ".join(old_hosts)
    )
    logger.debug(CLI_DEBUG_MSG, command)
    pexpect.run(command)
