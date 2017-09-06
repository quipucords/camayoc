# coding=utf-8
"""Tests for ``rho profile`` commands.

:caseautomation: automated
:casecomponent: profile
:caseimportance: high
:requirement: RHO
:testtype: functional
:upstream: yes
"""
import json
import random
from io import BytesIO
from pathlib import Path

import pexpect
import pytest

from camayoc import utils
from camayoc.tests.rho.utils import auth_add, input_vault_password


def test_add_with_auth_hosts(isolated_filesystem):
    """Add a profile with auth and hosts.

    :id: 51375fcd-c356-49a5-b192-6f222512d6b6
    :description: Add a profile entry providing the ``--name``, ``--auth`` and
        ``--hosts`` options.
    :steps: Run ``rho profile add --name <name> --auth <auth> --hosts <hosts>``
    :expectedresults: A new profile entry is created with the data provided as
        input.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0


def test_add_with_sshport(isolated_filesystem):
    """Add a profile with auth, hosts and port.

    :id: 487e0718-7553-4f8f-b454-a679dd34474c
    :description: Add a profile entry providing the ``--name``, ``--auth``,
        ``--hosts`` and ``--port`` options.
    :steps: Run ``rho profile add --name <name> --auth <auth> --hosts <hosts>
        --port <port>``
    :expectedresults: A new profile entry is created with the data provided as
        input.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    sshport = random.randint(0, 65535)
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {} --sshport {}'
        .format(name, auth_name, hosts, sshport)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "{}"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name, sshport)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0


def test_add_with_sshport_negative(isolated_filesystem):
    """Add a profile with auth, hosts and port.

    :id: d95702be-17f7-4938-9f38-b1bca36ee27b
    :description: Add a profile entry providing the ``--name``, ``--auth``,
        ``--hosts`` and ``--port`` options.
    :steps: Run ``rho profile add --name <name> --auth <auth> --hosts <hosts>
        --port <port>``
    :expectedresults: A new profile entry is created with the data provided as
        input.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    sshport = utils.uuid4()
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {} --sshport {}'
        .format(name, auth_name, hosts, sshport)
    )
    assert rho_profile_add.expect(
        'Port value {} should be a positive integer in the valid range '
        '\(0-65535\)'
        .format(sshport)
    ) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 1


def test_edit_auth(isolated_filesystem):
    """Edit a profile's auth.

    :id: 4f933b10-b6fc-43e1-8002-f4d77a95f4df
    :description: Edit the auth of a profile entry.
    :steps: Run ``rho profile edit --name <name> --auth <newauth>``
    :expectedresults: The profile's auth must be updated.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    new_auth_name = utils.uuid4()
    for auth_name in (auth_name, new_auth_name):
        auth_add(
            {
                'name': auth_name,
                'username': utils.uuid4(),
                'sshkeyfile': utils.uuid4(),
            },
        )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --auth {}'
        .format(name, new_auth_name)
    )
    input_vault_password(rho_profile_edit)
    assert rho_profile_edit.expect('Profile \'{}\' edited'.format(name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(new_auth_name, hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0


def test_edit_auth_negative(isolated_filesystem):
    """Edit the auth of a not created profile entry.

    :id: 39068134-784b-4451-853c-4d0a067434d4
    :description: Edit the auth of a not created profile entry.
    :steps: Run ``rho profile edit --name <invalidname> --auth <newauth>``
    :expectedresults: The command should fail with a proper message.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    invalid_name = utils.uuid4()
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --auth {}'
        .format(invalid_name, utils.uuid4())
    )
    input_vault_password(rho_profile_edit)
    rho_profile_edit.logfile = BytesIO()
    assert rho_profile_edit.expect(
        'Profile \'{}\' does not exist.'.format(invalid_name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 1


def test_edit_hosts(isolated_filesystem):
    """Edit a profile's hosts.

    :id: 994aa922-e132-4b01-bec2-a8cea987fb74
    :description: Edit the hosts of a profile entry.
    :steps: Run ``rho profile edit --name <name> --hosts <newhosts>``
    :expectedresults: The profile's hosts must be updated.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    new_hosts = '127.0.0.{}'.format(random.randint(2, 255))
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --hosts {}'
        .format(name, new_hosts)
    )
    input_vault_password(rho_profile_edit)
    assert rho_profile_edit.expect('Profile \'{}\' edited'.format(name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(auth_name, new_hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0


def test_edit_hosts_negative(isolated_filesystem):
    """Edit the hosts of a not created profile entry.

    :id: 99913d02-c06b-4012-8059-30b694af82fa
    :description: Edit the hosts of a not created profile entry.
    :steps: Run ``rho profile edit --name <invalidname> --hosts <newhosts>``
    :expectedresults: The command should fail with a proper message.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    new_hosts = '127.0.0.{}'.format(random.randint(2, 255))
    invalid_name = utils.uuid4()
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --hosts {}'
        .format(invalid_name, new_hosts)
    )
    input_vault_password(rho_profile_edit)
    rho_profile_edit.logfile = BytesIO()
    assert rho_profile_edit.expect(
        'Profile \'{}\' does not exist.'.format(invalid_name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 1


def test_edit_sshport(isolated_filesystem):
    """Edit a profile's sshport.

    :id: df269ca1-107b-4ee1-a671-107f5dfc5eb5
    :description: Edit the sshport of a profile entry.
    :steps: Run ``rho profile edit --name <name> --sshport <newsshport>``
    :expectedresults: The profile's sshport must be updated.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    sshport = new_sshport = random.randint(0, 65535)
    while sshport == new_sshport:
        new_sshport = random.randint(0, 65535)
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {} --sshport {}'
        .format(name, auth_name, hosts, sshport)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "{}"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name, sshport)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --sshport {}'
        .format(name, new_sshport)
    )
    input_vault_password(rho_profile_edit)
    assert rho_profile_edit.expect('Profile \'{}\' edited'.format(name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "{}"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name, new_sshport)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0


def test_edit_sshport_negative(isolated_filesystem):
    """Edit the sshport of a not created profile entry.

    :id: 8ad0f786-c982-40e7-97b6-7705f66cb749
    :description: Edit the sshport of a not created profile entry.
    :steps: Run ``rho profile edit --name <invalidname> --sshport
        <newsshport>``
    :expectedresults: The command should fail with a proper message.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    sshport = new_sshport = random.randint(0, 65535)
    while sshport == new_sshport:
        new_sshport = random.randint(0, 65535)
    invalid_name = utils.uuid4()
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {} --sshport {}'
        .format(name, auth_name, hosts, sshport)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_edit = pexpect.spawn(
        'rho profile edit --name {} --sshport {}'
        .format(invalid_name, new_sshport)
    )
    input_vault_password(rho_profile_edit)
    rho_profile_edit.logfile = BytesIO()
    assert rho_profile_edit.expect(
        'Profile \'{}\' does not exist.'.format(invalid_name)) == 0
    assert rho_profile_edit.expect(pexpect.EOF) == 0
    rho_profile_edit.close()
    assert rho_profile_edit.exitstatus == 1


def test_clear(isolated_filesystem):
    """Clear a profile.

    :id: 026644a5-4dd6-498c-9585-d7419016df6d
    :description: Clear a profile entry by entering the ``--name`` of an
        already created entry.
    :steps: Run ``rho profile clear --name <name>``
    :expectedresults: The profile entry is removed.
    """
    auth_name = utils.uuid4()
    name = utils.uuid4()
    hosts = '127.0.0.1'
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect('Profile "{}" was added'.format(name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        '{{\r\n'
        '    "auth": \[\r\n'
        '        {{\r\n'
        '            "id": ".*",\r\n'
        '            "name": "{}"\r\n'
        '        }}\r\n'
        '    \],\r\n'
        '    "hosts": \[\r\n'
        '        "{}"\r\n'
        '    \],\r\n'
        '    "name": "{}",\r\n'
        '    "ssh_port": "22"\r\n'
        '}}\r\n'
        .format(auth_name, hosts, name)
    ) == 0, rho_profile_show.stdout
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()
    assert rho_profile_show.exitstatus == 0

    # Create some files to mimic if the profile was used on a scan to check if
    # RHO will properly deal with them
    Path('rho/{}_hosts.yml'.format(name)).touch()
    Path('rho/{}_host_auth_mapping'.format(name)).touch()

    rho_profile_clear = pexpect.spawn(
        'rho profile clear --name={}'.format(name)
    )
    input_vault_password(rho_profile_clear)
    assert rho_profile_clear.expect(
        'Profile "{}" was removed'.format(name)
    ) == 0
    assert rho_profile_clear.expect(pexpect.EOF) == 0
    rho_profile_clear.close()
    assert rho_profile_clear.exitstatus == 0

    rho_profile_clear = pexpect.spawn(
        'rho profile clear --name={}'.format(name)
    )
    input_vault_password(rho_profile_clear)
    assert rho_profile_clear.expect(
        'No such profile: \'{}\''.format(name)
    ) == 0
    assert rho_profile_clear.expect(pexpect.EOF) == 0
    rho_profile_clear.close()
    assert rho_profile_clear.exitstatus == 1

    rho_profile_show = pexpect.spawn(
        'rho profile show --name={}'.format(name)
    )
    input_vault_password(rho_profile_show)
    assert rho_profile_show.expect(
        'Profile \'{}\' does not exist.'.format(name)
    ) == 0
    assert rho_profile_show.expect(pexpect.EOF) == 0
    rho_profile_show.close()

    # Check if RHO dealt with the created files.
    assert not Path('rho/{}_hosts.yml'.format(name)).exists()
    assert not Path('rho/{}_host_auth_mapping'.format(name)).exists()
    assert Path(
        'rho/(DELETED PROFILE){}_host_auth_mapping'.format(name)).exists()


@pytest.mark.parametrize('option', ('--name', '--all'))
def test_clear_no_profiles(isolated_filesystem, option):
    """Clear profiles no profiles were created.

    :id: 46a60d62-1797-4a75-b995-929b911486ae
    :description: Clear profiles by either providing the ``--name`` or
        ``--all`` options when no profiles are created.
    :steps:
        1. Ensure an empty RHO data dir
        2. Run ``rho profile clear --name <name>`` or ``rho profile clear
           --all``.
    :expectedresults: A message stating that all network profiles were removed.
    """
    if option == '--name':
        option = '{}={}'.format(option, utils.uuid4())
    rho_profile_clear = pexpect.spawn(
        'rho profile clear {}'.format(option)
    )
    assert rho_profile_clear.expect('All network profiles removed') == 0
    assert rho_profile_clear.expect(pexpect.EOF) == 0
    rho_profile_clear.close()
    assert rho_profile_clear.exitstatus == 0


def test_clear_negative(isolated_filesystem):
    """Clear a profile which is not created.

    :id: f8775db3-8343-4922-b93e-e39f9716e29c
    :description: Try to clear one profile entry by entering the ``--name`` of
        a not created entry.
    :steps: Run ``rho profile clear --name <invalidname>``
    :expectedresults: The command alerts that the profile is not created and
        can't be removed.
    """
    name = utils.uuid4()
    rho_profile_clear = pexpect.spawn(
        'rho profile clear --name={}'.format(name)
    )
    rho_profile_clear.logfile = BytesIO()
    assert rho_profile_clear.expect(pexpect.EOF) == 0
    assert (
        rho_profile_clear.logfile.getvalue().strip() ==
        b'All network profiles removed'
    )
    rho_profile_clear.logfile.close()
    rho_profile_clear.close()
    assert rho_profile_clear.exitstatus == 0


def test_clear_all(isolated_filesystem):
    """Clear all profiles.

    :id: 01a428b3-eda2-4162-a933-7acc30801e76
    :description: Clear multiple profile entries using the ``--all`` option.
    :steps: Run ``rho profile clear --all``
    :expectedresults: All profile entries are removed.
    """
    auth_name = utils.uuid4()
    auth_add(
        {
            'name': auth_name,
            'username': utils.uuid4(),
            'sshkeyfile': utils.uuid4(),
        },
    )
    profiles = []
    for _ in range(random.randint(2, 3)):
        name = utils.uuid4()
        hosts = '127.0.0.1'
        profile = {
            'auth': [{'name': auth_name}],
            'hosts': [hosts],
            'name': name,
            'ssh_port': '22',
        }
        profiles.append(profile)
        rho_profile_add = pexpect.spawn(
            'rho profile add --name {} --auth {} --hosts {}'
            .format(name, auth_name, hosts)
        )
        input_vault_password(rho_profile_add)
        assert rho_profile_add.expect(
            'Profile "{}" was added'.format(name)) == 0
        assert rho_profile_add.expect(pexpect.EOF) == 0
        rho_profile_add.close()
        assert rho_profile_add.exitstatus == 0

        # Create some files to mimic if the profile was used on a scan to check
        # if RHO will properly deal with them
        Path('rho/{}_hosts.yml'.format(name)).touch()
        Path('rho/{}_host_auth_mapping'.format(name)).touch()

    rho_profile_list = pexpect.spawn('rho profile list')
    input_vault_password(rho_profile_list)
    logfile = BytesIO()
    rho_profile_list.logfile = logfile
    assert rho_profile_list.expect(pexpect.EOF) == 0
    rho_profile_list.close()
    assert rho_profile_list.exitstatus == 0

    output = json.loads(logfile.getvalue().decode('utf-8'))
    logfile.close()

    for profile in output:
        del profile['auth'][0]['id']
    assert profiles == output

    rho_profile_clear = pexpect.spawn(
        'rho profile clear --all'
    )
    assert rho_profile_clear.expect('All network profiles removed') == 0
    assert rho_profile_clear.expect(pexpect.EOF) == 0
    rho_profile_clear.close()
    assert rho_profile_clear.exitstatus == 0

    for name in [profile['name'] for profile in profiles]:
        # Check if RHO dealt with the created files.
        assert not Path('rho/{}_hosts.yml'.format(name)).exists()
        assert not Path('rho/{}_host_auth_mapping'.format(name)).exists()
        assert Path(
            'rho/(DELETED PROFILE){}_host_auth_mapping'.format(name)).exists()

    rho_profile_list = pexpect.spawn('rho profile list')
    input_vault_password(rho_profile_list)
    assert rho_profile_list.expect('No profiles exist yet.') == 0
    assert rho_profile_list.expect(pexpect.EOF) == 0
    rho_profile_list.close()
    assert rho_profile_list.exitstatus == 1
