# coding=utf-8
"""Tests for ``qpc cred`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import random
from io import BytesIO
from pathlib import Path

import pexpect

from camayoc import utils
from camayoc.constants import (
    CONNECTION_PASSWORD_INPUT,
    MASKED_PASSWORD_OUTPUT,
    BECOME_PASSWORD_INPUT,
)
from camayoc.tests.qcs.cli.utils import cred_add, cred_show


def generate_show_output(data):
    """Generate a regex pattern with the data for a qpc cred show output."""
    output = '{\r\n'
    output += '    "become_method": "{}",\r\n'.format(
        data.get('become_method', 'sudo'))
    if 'become_password' in data:
        output += '    "become_password": "{}",\r\n'.format(
            data['become_password'])
    output += '    "become_user": "{}",\r\n'.format(
        data.get('become_user', 'root'))
    output += '    "cred_type": "{}",\r\n'.format(
        data.get('cred_type', 'network'))
    output += '    "id": {},\r\n'.format(data.get('id', '\\d+'))
    output += '    "name": "{}",\r\n'.format(data['name'])
    if 'password' in data:
        output += '    "password": "{}",\r\n'.format(data['password'])
    if 'ssh_keyfile' in data:
        output += '    "ssh_keyfile": "{}",\r\n'.format(data['ssh_keyfile'])
    output += '    "username": "{}"\r\n'.format(data['username'])
    output += '}\r\n'
    return output


def test_add_with_username_password(isolated_filesystem, qpc_server_config):
    """Add an auth with username and password.

    :id: c935d34c-54f6-443f-a85c-344934bc0cfb
    :description: Add an auth entry providing the ``--name``, ``--username``
        and ``--pasword`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    cred_add(
        {
            'name': name,
            'username': username,
            'password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'password': MASKED_PASSWORD_OUTPUT,
            'username': username,
        })
    )


def test_add_with_username_password_become_password(
        isolated_filesystem, qpc_server_config):
    """Add an auth with username, password and become password.

    :id: df0d61d5-363f-400a-961c-04146f6089e1
    :description: Add an auth entry providing the ``--name``, ``--username``,
        ``--pasword`` and ``--become-password`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --password
        --become-password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    cred_add(
        {
            'name': name,
            'username': username,
            'password': None,
            'become-password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, utils.uuid4()),
            (BECOME_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    cred_show(
        {'name': name},
        generate_show_output({
            'become_password': MASKED_PASSWORD_OUTPUT,
            'name': name,
            'password': MASKED_PASSWORD_OUTPUT,
            'username': username,
        })
    )


def test_add_with_username_sshkeyfile(isolated_filesystem, qpc_server_config):
    """Add an auth with username and sshkeyfile.

    :id: 9bfb16a2-5a10-4a01-9f9d-b29445c1f4bf
    :description: Add an auth entry providing the ``--name``, ``--username``
        and ``--sshkeyfile`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --sshkeyfile
        <sshkeyfile>``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )


def test_add_with_username_sshkeyfile_become_password(
        isolated_filesystem, qpc_server_config):
    """Add an auth with username, sshkeyfile and become password.

    :id: 94a45a9b-cda7-41e7-8be5-caf598917ebb
    :description: Add an auth entry providing the ``--name``, ``--username``,
        ``--sshkeyfile`` and ``--become-password`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --sshkeyfile
        <sshkeyfile> --become-password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add(
        {
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile.name,
            'become-password': None,
        },
        [
            (BECOME_PASSWORD_INPUT, utils.uuid4()),
        ]
    )

    cred_show(
        {'name': name},
        generate_show_output({
            'become_password': MASKED_PASSWORD_OUTPUT,
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )


def test_edit_username(isolated_filesystem, qpc_server_config):
    """Edit an auth's username.

    :id: 69e2d06e-5c29-42ab-916e-e724451afabe
    :description: Edit the username of an auth entry.
    :steps: Run ``qpc cred edit --name <name> --username <newusername>``
    :expectedresults: The auth username must be updated and the ``credentials``
        file must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    new_username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )

    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --username={}'.format(name, new_username)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect(
        'Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': new_username,
        })
    )


def test_edit_username_negative(isolated_filesystem, qpc_server_config):
    """Edit the username of a not created auth entry.

    :id: 97f0d71a-37d6-41d1-a5a1-f24ce4ca05bc
    :description: Edit the username of a not created auth entry.
    :steps: Run ``qpc cred edit --name <invalidname> --username <newusername>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    name = utils.uuid4()
    username = utils.uuid4()
    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --username={}'.format(name, username)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect(
        'Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_edit_password(isolated_filesystem, qpc_server_config):
    """Edit an auth's password.

    :id: 07bbe78d-d140-449d-b835-59b35d9e9a59
    :description: Edit the password of an auth entry.
    :steps: Run ``qpc cred edit --name <name> --password <newpassword>``
    :expectedresults: The auth password must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    password = utils.uuid4()
    new_password = utils.uuid4()
    cred_add(
        {
            'name': name,
            'username': username,
            'password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, password),
        ],
    )

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'password': MASKED_PASSWORD_OUTPUT,
            'username': username,
        })
    )

    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --password'.format(name, new_password)
    )
    assert qpc_cred_edit.expect(CONNECTION_PASSWORD_INPUT) == 0
    qpc_cred_edit.sendline(new_password)
    assert qpc_cred_edit.expect(
        'Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'password': MASKED_PASSWORD_OUTPUT,
            'username': username,
        })
    )


def test_edit_password_negative(isolated_filesystem, qpc_server_config):
    """Edit the password of a not created auth entry.

    :id: 34a39107-bfe1-489b-815b-fe2d9b15288c
    :description: Edit the password of a not created auth entry.
    :steps: Run ``qpc cred edit --name <invalidname> --password
        <newpassword>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    name = utils.uuid4()
    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --password'.format(name)
    )
    assert qpc_cred_edit.expect(
        'Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_edit_sshkeyfile(isolated_filesystem, qpc_server_config):
    """Edit an auth's sshkeyfile.

    :id: 81975705-bc77-4d1c-a8dd-72d1b996e19d
    :description: Edit the sshkeyfile of an auth entry.
    :steps: Run ``qpc cred edit --name <name> --sshkeyfile <newsshkeyfile>``
    :expectedresults: The auth sshkeyfile must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    new_sshkeyfile = Path(utils.uuid4())
    new_sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )

    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --sshkeyfile {}'
        .format(name, new_sshkeyfile.name)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect(
        'Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': new_sshkeyfile.resolve(),
            'username': username,
        })
    )


def test_edit_sshkeyfile_negative(isolated_filesystem, qpc_server_config):
    """Edit the sshkeyfile of a not created auth entry.

    :id: 97734b67-3d5e-4add-9282-22844fd436d1
    :description: Edit the sshkeyfile of a not created auth entry.
    :steps: Run ``qpc cred edit --name <invalidname> --sshkeyfile
        <newsshkeyfile>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    name = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --sshkeyfile {}'.format(name, sshkeyfile.name)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect(
        'Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_edit_become_password(isolated_filesystem, qpc_server_config):
    """Edit an auth's become password.

    :id: e1230ce5-7cb5-40d5-8f50-ff33779eee9e
    :description: Edit the password of an auth entry.
    :steps: Run ``qpc cred edit --name <name> --become-password``
    :expectedresults: The auth become password must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    become_password = utils.uuid4()
    new_become_password = utils.uuid4()
    cred_add(
        {
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile.name,
            'become-password': None,
        },
        [
            (BECOME_PASSWORD_INPUT, become_password),
        ],
    )

    cred_show(
        {'name': name},
        generate_show_output({
            'become_password': MASKED_PASSWORD_OUTPUT,
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )

    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --become-password'
        .format(name, new_become_password)
    )
    assert qpc_cred_edit.expect(BECOME_PASSWORD_INPUT) == 0
    qpc_cred_edit.sendline(new_become_password)
    assert qpc_cred_edit.expect(
        'Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show(
        {'name': name},
        generate_show_output({
            'become_password': MASKED_PASSWORD_OUTPUT,
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )


def test_edit_become_password_negative(isolated_filesystem, qpc_server_config):
    """Edit the become password of a not created auth entry.

    :id: 6364d80b-97b1-404e-85fd-76eebb7c6b5e
    :description: Edit the become password of a not created auth entry.
    :steps: Run ``qpc cred edit --name <invalidname> --become-password``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    name = utils.uuid4()
    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --become-password'.format(name)
    )
    assert qpc_cred_edit.expect(
        'Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_edit_no_credentials(isolated_filesystem, qpc_server_config):
    """Edit with no credentials created.

    :id: d5402714-98fe-4468-b841-8b450e65ac34
    :description: Edit any field of a not created auth entry when no
        credentials where privously created.
    :steps: Run ``qpc cred edit --name <invalidname> --sshkeyfile
        <sshkeyfile>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    qpc_cred_edit = pexpect.spawn(
        'qpc cred edit --name={} --sshkeyfile {}'.format(name, sshkeyfile.name)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect(
        'Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_clear(isolated_filesystem, qpc_server_config):
    """Clear an auth.

    :id: 550acd7f-0e2a-419c-a996-818b8475532f
    :description: Clear one auth entry by entering the ``--name`` of an already
        created entry.
    :steps: Run ``qpc cred clear --name <name>``
    :expectedresults: The auth entry is removed.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    cred_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile.name,
    })

    cred_show(
        {'name': name},
        generate_show_output({
            'name': name,
            'ssh_keyfile': sshkeyfile.resolve(),
            'username': username,
        })
    )

    qpc_cred_clear = pexpect.spawn(
        'qpc cred clear --name={}'.format(name)
    )
    assert qpc_cred_clear.expect(
        'Credential "{}" was removed'.format(name)) == 0
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 0

    qpc_cred_show = pexpect.spawn(
        'qpc cred show --name={}'.format(name)
    )
    assert qpc_cred_show.expect(
        'Credential "{}" does not exist'.format(name)
    ) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()


def test_clear_negative(isolated_filesystem, qpc_server_config):
    """Clear an auth which is not created.

    :id: eb15c629-e292-4f8a-90cd-51c65a566a20
    :description: Try to clear one auth entry by entering the ``--name`` of a
        not created entry.
    :steps: Run ``qpc cred clear --name <invalidname>``
    :expectedresults: The command alerts that the auth is not created and can't
        be removed.
    """
    name = utils.uuid4()
    qpc_cred_clear = pexpect.spawn(
        'qpc cred clear --name={}'.format(name)
    )
    qpc_cred_clear.logfile = BytesIO()
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    assert (
        qpc_cred_clear.logfile.getvalue().strip().decode('utf-8') ==
        'Credential "{}" was not found.'.format(name)
    )
    qpc_cred_clear.logfile.close()
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 1


def test_clear_all(isolated_filesystem, qpc_server_config):
    """Clear all auth entries.

    :id: 16aa6914-e7ae-400f-b12b-6c9d218c4e0f
    :description: Clear multiple auth entries using the ``--all`` option.
    :steps: Run ``qpc cred clear --all``
    :expectedresults: All auth entries are removed.
    """
    auths = []
    for _ in range(random.randint(2, 3)):
        name = utils.uuid4()
        username = utils.uuid4()
        sshkeyfile = Path(utils.uuid4())
        sshkeyfile.touch()
        auth = {
            'name': name,
            'password': None,
            'ssh_keyfile': str(sshkeyfile.resolve()),
            'become_password': None,
            'username': username,
        }
        auths.append(auth)
        cred_add({
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile.name,
        })

    qpc_cred_clear = pexpect.spawn(
        'qpc cred clear --all'
    )
    assert qpc_cred_clear.expect('All credentials were removed') == 0
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 0

    qpc_cred_list = pexpect.spawn('qpc cred list')
    assert qpc_cred_list.expect('No credentials exist yet.') == 0
    assert qpc_cred_list.expect(pexpect.EOF) == 0
    qpc_cred_list.close()
    assert qpc_cred_list.exitstatus == 0
