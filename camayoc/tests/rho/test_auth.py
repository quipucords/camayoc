# coding=utf-8
"""Tests for ``rho auth`` commands.

:caseautomation: automated
:casecomponent: auth
:caseimportance: high
:requirement: RHO
:testtype: functional
:upstream: yes
"""
import json
import random
from io import BytesIO

import pexpect

from camayoc import utils
from camayoc.constants import (
    CONNECTION_PASSWORD_INPUT,
    MASKED_PASSWORD_OUTPUT,
    SUDO_PASSWORD_INPUT,
)
from camayoc.tests.rho.utils import auth_add, input_vault_password


def test_add_with_username_password(isolated_filesystem):
    """Add an auth with username and password.

    :id: 2c0e5930-6ebb-4ac1-bca2-6214e132e748
    :description: Add an auth entry providing the ``--name``, ``--username``
        and ``--pasword`` options.
    :steps: Run ``rho auth add --name <name> --username <username> --password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    auth_add(
        {
            'name': name,
            'username': username,
            'password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": "{}",\r\n'
        '    "ssh_key_file": null,\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, MASKED_PASSWORD_OUTPUT, username)
    ) == 0, rho_auth_show.stdout
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_add_with_username_password_sudo_password(isolated_filesystem):
    """Add an auth with username, password and sudo password.

    :id: 34d3d28e-b15f-4dc7-a4da-2e3e879742d2
    :description: Add an auth entry providing the ``--name``, ``--username``,
        ``--pasword`` and ``--sudo-password`` options.
    :steps: Run ``rho auth add --name <name> --username <username> --password
        --sudo-password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    auth_add(
        {
            'name': name,
            'username': username,
            'password': None,
            'sudo-password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, utils.uuid4()),
            (SUDO_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": "{}",\r\n'
        '    "ssh_key_file": null,\r\n'
        '    "sudo_password": "{}",\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, MASKED_PASSWORD_OUTPUT, MASKED_PASSWORD_OUTPUT, username)
    ) == 0, rho_auth_show.stdout
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_add_with_username_sshkeyfile(isolated_filesystem):
    """Add an auth with username and sshkeyfile.

    :id: 0f709bf8-a1bf-4181-a392-428e6d9400b3
    :description: Add an auth entry providing the ``--name``, ``--username``
        and ``--sshkeyfile`` options.
    :steps: Run ``rho auth add --name <name> --username <username> --sshkeyfile
        <sshkeyfile>``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_add_with_username_sshkeyfile_sudo_password(isolated_filesystem):
    """Add an auth with username, sshkeyfile and sudo password.

    :id: c70b3a8e-1390-4a9d-a693-1eb410751f66
    :description: Add an auth entry providing the ``--name``, ``--username``,
        ``--sshkeyfile`` and ``--sudo-password`` options.
    :steps: Run ``rho auth add --name <name> --username <username> --sshkeyfile
        <sshkeyfile> --sudo-password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add(
        {
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile,
            'sudo-password': None,
        },
        [
            (SUDO_PASSWORD_INPUT, utils.uuid4()),
        ]
    )

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": "{}",\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, MASKED_PASSWORD_OUTPUT, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_edit_username(isolated_filesystem):
    """Edit an auth's username.

    :id: 3849423c-60cd-473b-a305-7359a2d3477d
    :description: Edit the username of an auth entry.
    :steps: Run ``rho auth edit --name <name> --username <newusername>``
    :expectedresults: The auth username must be updated and the ``credentials``
        file must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    new_username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0

    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --username={}'.format(name, new_username)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect('Auth \'{}\' updated'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus == 0

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, new_username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_edit_username_negative(isolated_filesystem):
    """Edit the username of a not created auth entry.

    :id: 66abc87b-0e1b-4033-aae3-876f89aadfe3
    :description: Edit the username of a not created auth entry.
    :steps: Run ``rho auth edit --name <invalidname> --username <newusername>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    name = utils.uuid4()
    username = utils.uuid4()
    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --username={}'.format(name, username)
    )
    input_vault_password(rho_auth_edit)
    rho_auth_edit.logfile = BytesIO()
    assert rho_auth_edit.expect('Auth "{}" does not exist'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus != 0


def test_edit_password(isolated_filesystem):
    """Edit an auth's password.

    :id: 78c80041-ad2c-461a-8d70-d4ee71645e93
    :description: Edit the password of an auth entry.
    :steps: Run ``rho auth edit --name <name> --password <newpassword>``
    :expectedresults: The auth password must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    password = utils.uuid4()
    new_password = utils.uuid4()
    auth_add(
        {
            'name': name,
            'username': username,
            'password': None,
        },
        [
            (CONNECTION_PASSWORD_INPUT, password),
        ],
    )

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": "{}",\r\n'
        '    "ssh_key_file": null,\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, MASKED_PASSWORD_OUTPUT, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0

    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --password'.format(name, new_password)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect(CONNECTION_PASSWORD_INPUT) == 0
    rho_auth_edit.sendline(new_password)
    assert rho_auth_edit.expect('Auth \'{}\' updated'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus == 0

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": "{}",\r\n'
        '    "ssh_key_file": null,\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, MASKED_PASSWORD_OUTPUT, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_edit_password_negative(isolated_filesystem):
    """Edit the password of a not created auth entry.

    :id: 3469c05d-2dee-4b5a-84a8-e9f3ce391480
    :description: Edit the password of a not created auth entry.
    :steps: Run ``rho auth edit --name <invalidname> --password
        <newpassword>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    name = utils.uuid4()
    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --password'.format(name)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect('Auth "{}" does not exist'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus != 0


def test_edit_sshkeyfile(isolated_filesystem):
    """Edit an auth's sshkeyfile.

    :id: 557dfcd0-56d8-4d82-bdd0-42caef5691a8
    :description: Edit the sshkeyfile of an auth entry.
    :steps: Run ``rho auth edit --name <name> --sshkeyfile <newsshkeyfile>``
    :expectedresults: The auth sshkeyfile must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    new_sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0

    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --sshkeyfile {}'.format(name, new_sshkeyfile)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect('Auth \'{}\' updated'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus == 0

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, new_sshkeyfile, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_edit_sshkeyfile_negative(isolated_filesystem):
    """Edit the sshkeyfile of a not created auth entry.

    :id: 4c43d7af-5dd8-4a97-8d48-9cd2e611844e
    :description: Edit the sshkeyfile of a not created auth entry.
    :steps: Run ``rho auth edit --name <invalidname> --sshkeyfile
        <newsshkeyfile>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    name = utils.uuid4()
    sshkeyfile = utils.uuid4()
    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --sshkeyfile {}'.format(name, sshkeyfile)
    )
    input_vault_password(rho_auth_edit)
    rho_auth_edit.logfile = BytesIO()
    assert rho_auth_edit.expect('Auth "{}" does not exist'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus != 0


def test_edit_sudo_password(isolated_filesystem):
    """Edit an auth's sudo password.

    :id: 3f2f7393-41c6-42eb-913e-a19213f5d586
    :description: Edit the password of an auth entry.
    :steps: Run ``rho auth edit --name <name> --sudo-password``
    :expectedresults: The auth sudo password must be updated.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    sudo_password = utils.uuid4()
    new_sudo_password = utils.uuid4()
    auth_add(
        {
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile,
            'sudo-password': None,
        },
        [
            (SUDO_PASSWORD_INPUT, sudo_password),
        ],
    )

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": "{}",\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, MASKED_PASSWORD_OUTPUT, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0

    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --sudo-password'
        .format(name, new_sudo_password)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect(SUDO_PASSWORD_INPUT) == 0
    rho_auth_edit.sendline(new_sudo_password)
    assert rho_auth_edit.expect('Auth \'{}\' updated'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus == 0

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": "{}",\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, MASKED_PASSWORD_OUTPUT, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0


def test_edit_sudo_password_negative(isolated_filesystem):
    """Edit the sudo password of a not created auth entry.

    :id: abe8f6f3-6c45-42a1-abcf-ffd6952cf886
    :description: Edit the sudo password of a not created auth entry.
    :steps: Run ``rho auth edit --name <invalidname> --sudo-password``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    name = utils.uuid4()
    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --sudo-password'.format(name)
    )
    input_vault_password(rho_auth_edit)
    assert rho_auth_edit.expect('Auth "{}" does not exist'.format(name)) == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus != 0


def test_edit_no_credentials(isolated_filesystem):
    """Edit with no credentials created.

    :id: 20725fc8-722e-498c-b035-ccc8498e44f5
    :description: Edit any field of a not created auth entry when no
        credentials where privously created.
    :steps: Run ``rho auth edit --name <invalidname> --sshkeyfile
        <sshkeyfile>``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    sshkeyfile = utils.uuid4()
    rho_auth_edit = pexpect.spawn(
        'rho auth edit --name={} --sshkeyfile {}'.format(name, sshkeyfile)
    )
    input_vault_password(rho_auth_edit)
    rho_auth_edit.logfile = BytesIO()
    assert rho_auth_edit.expect('No auth credentials found') == 0
    assert rho_auth_edit.expect(pexpect.EOF) == 0
    rho_auth_edit.close()
    assert rho_auth_edit.exitstatus != 0


def test_clear(isolated_filesystem):
    """Clear an auth.

    :id: be4270b0-1c28-4b16-b602-02ba3759c254
    :description: Clear one auth entry by entering the ``--name`` of an already
        created entry.
    :steps: Run ``rho auth clear --name <name>``
    :expectedresults: The auth entry is removed.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = utils.uuid4()
    auth_add({
        'name': name,
        'username': username,
        'sshkeyfile': sshkeyfile,
    })

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        '{{\r\n'
        '    "id": "(.*)",\r\n'
        '    "name": "{}",\r\n'
        '    "password": null,\r\n'
        '    "ssh_key_file": "{}",\r\n'
        '    "sudo_password": null,\r\n'
        '    "username": "{}"\r\n'
        '}}\r\n'
        .format(name, sshkeyfile, username)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()
    assert rho_auth_show.exitstatus == 0

    rho_auth_clear = pexpect.spawn(
        'rho auth clear --name={}'.format(name)
    )
    input_vault_password(rho_auth_clear)
    assert rho_auth_clear.expect('Auth "{}" was removed'.format(name)) == 0
    assert rho_auth_clear.expect(pexpect.EOF) == 0
    rho_auth_clear.close()
    assert rho_auth_clear.exitstatus == 0

    rho_auth_show = pexpect.spawn(
        'rho auth show --name={}'.format(name)
    )
    input_vault_password(rho_auth_show)
    assert rho_auth_show.expect(
        'Auth "{}" does not exist'.format(name)
    ) == 0
    assert rho_auth_show.expect(pexpect.EOF) == 0
    rho_auth_show.close()


def test_clear_negative(isolated_filesystem):
    """Clear an auth which is not created.

    :id: 64cac5ae-eb90-4c38-8312-3181c18ed8a8
    :description: Try to clear one auth entry by entering the ``--name`` of a
        not created entry.
    :steps: Run ``rho auth clear --name <invalidname>``
    :expectedresults: The command alerts that the auth is not created and can't
        be removed.
    """
    name = utils.uuid4()
    rho_auth_clear = pexpect.spawn(
        'rho auth clear --name={}'.format(name)
    )
    input_vault_password(rho_auth_clear)
    rho_auth_clear.logfile = BytesIO()
    assert rho_auth_clear.expect(pexpect.EOF) == 0
    assert (
        rho_auth_clear.logfile.getvalue().strip() ==
        b'All authorization credentials removed'
    )
    rho_auth_clear.logfile.close()
    rho_auth_clear.close()
    assert rho_auth_clear.exitstatus == 0


def test_clear_all(isolated_filesystem):
    """Clear all auth entries.

    :id: 1110b433-b5a2-45d3-bd7d-8440ae2a0bf8
    :description: Clear multiple auth entries using the ``--all`` option.
    :steps: Run ``rho auth clear --all``
    :expectedresults: All auth entries are removed.
    """
    auths = []
    for _ in range(random.randint(2, 3)):
        name = utils.uuid4()
        username = utils.uuid4()
        sshkeyfile = utils.uuid4()
        auth = {
            'name': name,
            'password': None,
            'ssh_key_file': sshkeyfile,
            'sudo_password': None,
            'username': username,
        }
        auths.append(auth)
        auth_add({
            'name': name,
            'username': username,
            'sshkeyfile': sshkeyfile,
        })

    rho_auth_list = pexpect.spawn('rho auth list')
    input_vault_password(rho_auth_list)
    logfile = BytesIO()
    rho_auth_list.logfile = logfile
    assert rho_auth_list.expect(pexpect.EOF) == 0
    rho_auth_list.close()
    assert rho_auth_list.exitstatus == 0

    output = json.loads(logfile.getvalue().decode('utf-8'))
    logfile.close()

    for auth in output:
        del auth['id']
    assert auths == output

    rho_auth_clear = pexpect.spawn(
        'rho auth clear --all'
    )
    assert rho_auth_clear.expect('All authorization credentials removed') == 0
    assert rho_auth_clear.expect(pexpect.EOF) == 0
    rho_auth_clear.close()
    assert rho_auth_clear.exitstatus == 0

    rho_auth_list = pexpect.spawn('rho auth list')
    input_vault_password(rho_auth_list)
    assert rho_auth_list.expect('No credentials exist yet.') == 0
    assert rho_auth_list.expect(pexpect.EOF) == 0
    rho_auth_list.close()
    assert rho_auth_list.exitstatus == 1
