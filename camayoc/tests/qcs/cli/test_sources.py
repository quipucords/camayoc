# coding=utf-8
"""Tests for ``qpc source`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import json
import random
from io import BytesIO

import pexpect
import pytest

from camayoc import utils
from camayoc.constants import CONNECTION_PASSWORD_INPUT, QCS_HOST_MANAGER_TYPES
from camayoc.tests.qcs.cli.utils import cred_add, source_show


ISSUE_449_MARK = pytest.mark.xfail(
    reason='https://github.com/quipucords/quipucords/issues/449', strict=True)

VALID_SOURCE_TYPE_HOSTS = (
    ('network', '192.168.0.42'),
    ('network', '192.168.0.1 192.168.0.2'),
    ('network', '192.168.0.0/24'),
    ('network', '192.168.0.[1:100]'),
    ('network', 'host.example.com'),
    ('vcenter', '192.168.0.42'),
    ('vcenter', 'vcenter.example.com'),
)


def default_port_for_source(source_type):
    """Resolve the default port for a given source type."""
    if source_type in QCS_HOST_MANAGER_TYPES:
        return 443
    else:
        return 22


def generate_show_output(data):
    """Generate a regex pattern with the data for a qpc cred show output."""
    output = '{\r\n'
    output += (
        '    "credentials": \[\r\n'
        '        {{\r\n'
        '            "id": \\d+,\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        .format(data['cred_name'])
    )
    output += (
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        .format(data['hosts'])
    )
    output += '    "id": \\d+,\r\n'
    output += '    "name": "{}",\r\n'.format(data['name'])
    source_type = data['source_type']
    if source_type == 'satellite':
        output += (
            '    "options": {{\r\n'
            '        "satellite_version": "{}",\r\n'
            '        "ssl_cert_verify": true\r\n'
            '    }},\r\n'
            .format(data.get('satellite_version', '6.2'))
        )
    if source_type == 'vcenter':
        output += (
            '    "options": {\r\n'
            '        "ssl_cert_verify": true\r\n'
            '    },\r\n'
        )
    output += '    "port": {},\r\n'.format(data['port'])
    output += '    "source_type": "{}"\r\n'.format(source_type)
    output += '}\r\n'
    return output


@pytest.mark.parametrize('source_type,hosts', VALID_SOURCE_TYPE_HOSTS)
def test_add_with_cred_hosts(
        isolated_filesystem, qpc_server_config, hosts, source_type):
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
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    if hosts.endswith('0/24'):
        hosts = hosts.replace('0/24', '\[0:255\]')
    elif hosts.endswith('[1:100]'):
        hosts = hosts.replace('[1:100]', '\[1:100\]')
    elif ' ' in hosts:
        hosts = '",\r\n        "'.join(hosts.split(' '))
    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )


@pytest.mark.parametrize('source_type,hosts', VALID_SOURCE_TYPE_HOSTS)
def test_add_with_cred_hosts_file(
        isolated_filesystem, qpc_server_config, hosts, source_type):
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
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    with open('hosts_file', 'w') as handler:
        handler.write(hosts.replace(' ', '\n') + '\n')

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, 'hosts_file', source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    if hosts.endswith('0/24'):
        hosts = hosts.replace('0/24', '\[0:255\]')
    elif hosts.endswith('[1:100]'):
        hosts = hosts.replace('[1:100]', '\[1:100\]')
    elif ' ' in hosts:
        hosts = '",\r\n        "'.join(hosts.split(' '))
    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
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
    hosts = '127.0.0.1'
    port = random.randint(0, 65535)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --port {} '
        '--type {}'
        .format(name, cred_name, hosts, port, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )


def test_add_with_port_negative(
        isolated_filesystem, qpc_server_config, source_type):
    """Add a source with cred, hosts and port.

    :id: 663693b9-5021-4ed0-b456-9e252b6945c0
    :description: Add a source entry providing the ``--name``, ``--cred``,
        ``--hosts`` and ``--port`` options.
    :steps: Run ``qpc source add --name <name> --cred <cred> --hosts <hosts>
        --port <port> --type <type>``
    :expectedresults: A new source entry is created with the data provided as
        input.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    port = utils.uuid4()
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --port {} --type {}'
        .format(name, cred_name, hosts, port, source_type)
    )
    assert qpc_source_add.expect(
        'Port value {} should be a positive integer in the valid range '
        '\(0-65535\)'
        .format(port)
    ) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 2


def test_edit_cred(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's cred.

    :id: 7f58fee6-0c67-4732-bff5-15d6adafed28
    :description: Edit the cred of a source entry.
    :steps: Run ``qpc source edit --name <name> --cred <newcred>``
    :expectedresults: The source's cred must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    new_cred_name = utils.uuid4()
    port = default_port_for_source(source_type)
    for cred_name in (cred_name, new_cred_name):
        cred_add(
            {
                'name': cred_name,
                'username': utils.uuid4(),
                'password': None,
                'type': source_type,
            },
            [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
        )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --cred {}'
        .format(name, new_cred_name)
    )
    assert qpc_source_edit.expect(
        'Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': new_cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )


def test_edit_cred_negative(
        isolated_filesystem, qpc_server_config, source_type):
    """Edit the cred of a source entry that does not exist.

    :id: 9450f9ec-875a-4f21-a8cb-94b8122b57cf
    :description: Edit the cred of a not created source entry.
    :steps: Run ``qpc source edit --name <invalidname> --cred <newcred>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    invalid_name = utils.uuid4()
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --cred {}'
        .format(invalid_name, utils.uuid4())
    )
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect(
        'Source "{}" does not exist.'.format(invalid_name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


@pytest.mark.parametrize('source_type,new_hosts', VALID_SOURCE_TYPE_HOSTS)
def test_edit_hosts(
        isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Edit a source's hosts.

    :id: bfc1d4a8-e4af-406f-a70e-46674fa2c1d0
    :description: Edit the hosts of a source entry.
    :steps: Run ``qpc source edit --name <name> --hosts <newhosts>``
    :expectedresults: The source's hosts must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --hosts {}'
        .format(name, new_hosts)
    )
    assert qpc_source_edit.expect(
        'Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    if new_hosts.endswith('0/24'):
        new_hosts = new_hosts.replace('0/24', '\[0:255\]')
    elif new_hosts.endswith('[1:100]'):
        new_hosts = new_hosts.replace('[1:100]', '\[1:100\]')
    elif ' ' in new_hosts:
        new_hosts = '",\r\n        "'.join(new_hosts.split(' '))
    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': new_hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )


@pytest.mark.parametrize('source_type,new_hosts', VALID_SOURCE_TYPE_HOSTS)
def test_edit_hosts_file(
        isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Edit a source's hosts.

    :id: aa759d0d-4f67-42a0-934d-6e99750da113
    :description: Edit the hosts of a source entry.
    :steps: Run ``qpc source edit --name <name> --hosts <newhosts>``
    :expectedresults: The source's hosts must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    qpc_source_add.logfile = BytesIO()
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )

    with open('hosts_file', 'w') as handler:
        handler.write(new_hosts.replace(' ', '\n') + '\n')

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --hosts {}'
        .format(name, 'hosts_file')
    )
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect(
        'Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    if new_hosts.endswith('0/24'):
        new_hosts = new_hosts.replace('0/24', '\[0:255\]')
    elif new_hosts.endswith('[1:100]'):
        new_hosts = new_hosts.replace('[1:100]', '\[1:100\]')
    elif ' ' in new_hosts:
        new_hosts = '",\r\n        "'.join(new_hosts.split(' '))
    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': new_hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )


@pytest.mark.parametrize(
    ('source_type,new_hosts'), (
        ('vcenter', '192.168.0.1 192.168.0.2'),
        ('vcenter', '192.168.0.0/24'),
        ('vcenter', '192.168.0.[1:100]'),
    )
)
def test_edit_hosts_negative(
        isolated_filesystem, qpc_server_config, new_hosts, source_type):
    """Try to edit the hosts of a source entry with invalid values.

    :id: 802d4a66-b0ee-4351-bff4-52469ed023f4
    :description: Edit the hosts of a source entry with invalid values. The
        command should fail and state the reason why the value is invalid.
    :steps: Run ``qpc source edit --name <name> --hosts <invalidhosts>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --hosts {}'
        .format(name, new_hosts)
    )
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect(
        'hosts: Source of type vcenter must have a single hosts.') == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


def test_edit_port(isolated_filesystem, qpc_server_config, source_type):
    """Edit a source's port.

    :id: dc218224-7618-4bec-abc6-39c904290c11
    :description: Edit the port of a source entry.
    :steps: Run ``qpc source edit --name <name> --port <newport>``
    :expectedresults: The source's port must be updated.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    port = new_port = random.randint(0, 65535)
    while port == new_port:
        new_port = random.randint(0, 65535)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --port {} --type {}'
        .format(name, cred_name, hosts, port, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --port {}'
        .format(name, new_port)
    )
    assert qpc_source_edit.expect(
        'Source "{}" was updated'.format(name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': new_port,
            'source_type': source_type,
        })
    )


def test_edit_port_negative(
        isolated_filesystem, qpc_server_config, source_type):
    """Edit port of a source entry that does not exist.

    :id: 1e6bf9f2-ee5a-44fa-a721-4c308ae4e32b
    :description: Edit the port of a not created source entry.
    :steps: Run ``qpc source edit --name <invalidname> --port
        <newport>``
    :expectedresults: The command should fail with a proper message.
    """
    cred_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    port = new_port = random.randint(0, 65535)
    while port == new_port:
        new_port = random.randint(0, 65535)
    invalid_name = utils.uuid4()
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --port {} --type {}'
        .format(name, cred_name, hosts, port, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    qpc_source_edit = pexpect.spawn(
        'qpc source edit --name {} --port {}'
        .format(invalid_name, new_port)
    )
    qpc_source_edit.logfile = BytesIO()
    assert qpc_source_edit.expect(
        'Source "{}" does not exist.'.format(invalid_name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 1


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
    hosts = '127.0.0.1'
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_add = pexpect.spawn(
        'qpc source add --name {} --cred {} --hosts {} --type {}'
        .format(name, cred_name, hosts, source_type)
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    source_show(
        {'name': name},
        generate_show_output({
            'cred_name': cred_name,
            'hosts': hosts,
            'name': name,
            'port': port,
            'source_type': source_type,
        })
    )

    qpc_source_clear = pexpect.spawn(
        'qpc source clear --name={}'.format(name)
    )
    assert qpc_source_clear.expect(
        'Source "{}" was removed'.format(name)
    ) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0

    qpc_source_clear = pexpect.spawn(
        'qpc source clear --name={}'.format(name)
    )
    assert qpc_source_clear.expect(
        'Source "{}" was not found.'.format(name)
    ) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 1

    qpc_source_show = pexpect.spawn(
        'qpc source show --name={}'.format(name)
    )
    assert qpc_source_show.expect(
        'Source "{}" does not exist.'.format(name)
    ) == 0
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
    qpc_source_clear = pexpect.spawn(
        'qpc source clear --name={}'.format(name)
    )
    qpc_source_clear.logfile = BytesIO()
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    assert (
        qpc_source_clear.logfile.getvalue().strip() ==
        'Source "{}" was not found.'.format(name).encode('utf-8')
    )
    qpc_source_clear.logfile.close()
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 1


def test_clear_all(isolated_filesystem, qpc_server_config, source_type):
    """Clear all sources.

    :id: 23234cc2-fb41-4bc4-973a-7c850b998467
    :description: Clear multiple source entries using the ``--all`` option.
    :steps: Run ``qpc source clear --all``
    :expectedresults: All source entries are removed.
    """
    cred_name = utils.uuid4()
    port = default_port_for_source(source_type)
    cred_add(
        {
            'name': cred_name,
            'username': utils.uuid4(),
            'password': None,
            'type': source_type,
        },
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    qpc_source_clear = pexpect.spawn(
        'qpc source clear --all'
    )
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus >= 0

    sources = []
    for _ in range(random.randint(2, 3)):
        name = utils.uuid4()
        hosts = '127.0.0.1'
        source = {
            'credentials': [{'name': cred_name}],
            'hosts': [hosts],
            'name': name,
            'port': port,
            'source_type': source_type,
        }
        if source_type == 'satellite':
            source['options'] = {
                'satellite_version': '6.2',
                'ssl_cert_verify': True,
            }
        if source_type == 'vcenter':
            source['options'] = {'ssl_cert_verify': True}
        sources.append(source)
        qpc_source_add = pexpect.spawn(
            'qpc source add --name {} --cred {} --hosts {} --type {}'
            .format(name, cred_name, hosts, source_type)
        )
        assert qpc_source_add.expect(
            'Source "{}" was added'.format(name)) == 0
        assert qpc_source_add.expect(pexpect.EOF) == 0
        qpc_source_add.close()
        assert qpc_source_add.exitstatus == 0

    qpc_source_list = pexpect.spawn('qpc source list')
    logfile = BytesIO()
    qpc_source_list.logfile = logfile
    assert qpc_source_list.expect(pexpect.EOF) == 0
    qpc_source_list.close()
    assert qpc_source_list.exitstatus == 0

    output = json.loads(logfile.getvalue().decode('utf-8'))
    logfile.close()

    for source in output:
        del source['credentials'][0]['id']
        del source['id']
    assert sources == output

    qpc_source_clear = pexpect.spawn(
        'qpc source clear --all'
    )
    assert qpc_source_clear.expect('All sources were removed') == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0

    qpc_source_list = pexpect.spawn('qpc source list')
    assert qpc_source_list.expect('No sources exist yet.') == 0
    assert qpc_source_list.expect(pexpect.EOF) == 0
    qpc_source_list.close()
    assert qpc_source_list.exitstatus == 0
