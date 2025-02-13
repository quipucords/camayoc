# coding=utf-8
"""Tests for ``qpc cred`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import json
import random
from io import BytesIO

import pexpect
import pytest
from littletable import Table

from camayoc import utils
from camayoc.constants import BECOME_PASSWORD_INPUT
from camayoc.constants import CONNECTION_PASSWORD_INPUT
from camayoc.constants import MASKED_PASSWORD_OUTPUT
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import cred_show_and_check
from camayoc.tests.qpc.cli.utils import source_add_and_check
from camayoc.tests.qpc.cli.utils import source_show
from camayoc.utils import client_cmd


def generate_show_output(data):
    """Generate a regex pattern with the data for a qpc cred show output."""
    cred_type = data.get("cred_type", "network")
    auth_type = data.get("auth_type", "(auth_token|password|ssh_key|ssh_keyfile|unknown)")
    output = "{\r\n"
    output += '    "auth_type": "{}",\r\n'.format(auth_type)
    output += '    "become_method": {},\r\n'.format(data.get("become_method", "null"))
    output += '    "become_user": {},\r\n'.format(data.get("become_user", "null"))
    output += '    "created_at": {},\r\n'.format(data.get("created_at", ".*"))
    output += '    "cred_type": "{}",\r\n'.format(cred_type)
    for field in ("auth_token", "become_password", "password", "ssh_key", "ssh_passphrase"):
        value = field in data
        output += '    "has_{}": {},\r\n'.format(field, str(value).lower())
    output += '    "id": {},\r\n'.format(data.get("id", "\\d+"))
    output += '    "name": "{}",\r\n'.format(data["name"])
    output += '    "sources": \\[.*\\],\r\n'
    output += '    "ssh_keyfile": {},\r\n'.format(data.get("ssh_keyfile", "null"))
    output += '    "updated_at": {},\r\n'.format(data.get("updated_at", ".*"))
    output += '    "username": "{}"\r\n'.format(data["username"])
    output += "}\r\n"
    return output


def test_add_with_username_password(isolated_filesystem, qpc_server_config, source_type):
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
    cred_add_and_check(
        {"name": name, "username": username, "password": None, "type": source_type},
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    extra_output_args = {}
    if source_type == "network":
        extra_output_args["become_method"] = '"sudo"'
        extra_output_args["become_user"] = '"root"'
    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": source_type,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                **extra_output_args,
            }
        ),
    )


def test_add_with_username_password_become_password(isolated_filesystem, qpc_server_config):
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
    cred_add_and_check(
        {"name": name, "username": username, "password": None, "become-password": None},
        [
            (CONNECTION_PASSWORD_INPUT, utils.uuid4()),
            (BECOME_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "become_method": '"sudo"',
                "become_user": '"root"',
                "become_password": MASKED_PASSWORD_OUTPUT,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
            }
        ),
    )


@pytest.mark.ssh_keyfile_path
def test_add_with_username_sshkeyfile(data_provider, qpc_server_config):
    """Add an auth with username and sshkeyfile.

    :id: 9bfb16a2-5a10-4a01-9f9d-b29445c1f4bf
    :description: Add an auth entry providing the ``--name``, ``--username``
        and ``--sshkeyfile`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --sshkey``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile_cred = data_provider.credentials.new_one(
        {"type": "network", "sshkeyfile": Table.is_not_null()},
        data_only=True,
    )

    cred_add_and_check(
        {"name": name, "username": username, "sshkey": None},
        inputs=[("Private SSH Key:", sshkeyfile_cred.ssh_key)],
    )

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "name": name,
                "ssh_key": True,
                "username": username,
                "auth_type": "ssh_key",
                "become_method": '"sudo"',
                "become_user": '"root"',
            }
        ),
    )


@pytest.mark.ssh_keyfile_path
def test_add_with_username_sshkeyfile_become_password(data_provider, qpc_server_config):
    """Add an auth with username, sshkeyfile and become password.

    :id: 94a45a9b-cda7-41e7-8be5-caf598917ebb
    :description: Add an auth entry providing the ``--name``, ``--username``,
        ``--sshkey`` and ``--become-password`` options.
    :steps: Run ``qpc cred add --name <name> --username <username> --sshkey
        --become-password``
    :expectedresults: A new auth entry is created with the data provided as
        input.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile_cred = data_provider.credentials.new_one(
        {"type": "network", "sshkeyfile": Table.is_not_null()},
        data_only=True,
    )

    cred_add_and_check(
        {
            "name": name,
            "username": username,
            "sshkey": None,
            "become-password": None,
        },
        inputs=[
            ("Private SSH Key:", sshkeyfile_cred.ssh_key),
            (BECOME_PASSWORD_INPUT, utils.uuid4()),
        ],
    )

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": "network",
                "become_method": '"sudo"',
                "become_user": '"root"',
                "become_password": MASKED_PASSWORD_OUTPUT,
                "name": name,
                "ssh_key": True,
                "username": username,
                "auth_type": "ssh_key",
            }
        ),
    )


def test_edit_username(isolated_filesystem, qpc_server_config, source_type):
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
    cred_add_and_check(
        {"name": name, "password": None, "type": source_type, "username": username},
        [(CONNECTION_PASSWORD_INPUT, utils.uuid4())],
    )

    extra_output_args = {}
    if source_type == "network":
        extra_output_args["become_method"] = '"sudo"'
        extra_output_args["become_user"] = '"root"'
    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": source_type,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                **extra_output_args,
            }
        ),
    )

    qpc_cred_edit = pexpect.spawn(
        "{} -v cred edit --name={} --username={}".format(client_cmd, name, new_username)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect('Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": source_type,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": new_username,
                "auth_type": "password",
                **extra_output_args,
            }
        ),
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
    password = utils.uuid4()
    cred_add_and_check(
        {"name": name, "username": username, "password": None},
        [("Password:", password)],
    )

    name = utils.uuid4()
    username = utils.uuid4()
    qpc_cred_edit = pexpect.spawn(
        "{} -v cred edit --name={} --username={}".format(client_cmd, name, username)
    )
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect('Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


def test_edit_password(isolated_filesystem, qpc_server_config, source_type):
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
    cred_add_and_check(
        {"name": name, "username": username, "password": None, "type": source_type},
        [(CONNECTION_PASSWORD_INPUT, password)],
    )

    extra_output_args = {}
    if source_type == "network":
        extra_output_args["become_method"] = '"sudo"'
        extra_output_args["become_user"] = '"root"'
    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": source_type,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                **extra_output_args,
            }
        ),
    )

    qpc_cred_edit = pexpect.spawn("{} -v cred edit --name={} --password".format(client_cmd, name))
    assert qpc_cred_edit.expect(CONNECTION_PASSWORD_INPUT) == 0
    qpc_cred_edit.sendline(new_password)
    assert qpc_cred_edit.expect('Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "cred_type": source_type,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                **extra_output_args,
            }
        ),
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
    password = utils.uuid4()
    cred_add_and_check(
        {"name": name, "username": username, "password": None},
        [("Password:", password)],
    )

    name = utils.uuid4()
    qpc_cred_edit = pexpect.spawn("{} -v cred edit --name={} --password".format(client_cmd, name))
    assert qpc_cred_edit.expect('Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus != 0


@pytest.mark.ssh_keyfile_path
def test_edit_sshkeyfile_negative(data_provider, qpc_server_config):
    """Edit the sshkeyfile of a not created auth entry.

    :id: 97734b67-3d5e-4add-9282-22844fd436d1
    :description: Edit the sshkeyfile of a not created auth entry.
    :steps: Run ``qpc cred edit --name <invalidname> --sshkey``
    :expectedresults: The command should fail with a proper message.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile_cred = data_provider.credentials.new_one(
        {"type": "network", "sshkeyfile": Table.is_not_null()},
        data_only=True,
    )
    cred_add_and_check(
        {"name": name, "username": username, "sshkey": None},
        inputs=[("Private SSH Key:", sshkeyfile_cred.ssh_key)],
    )

    name = utils.uuid4()
    qpc_cred_edit = pexpect.spawn("{} -v cred edit --name={} --sshkey".format(client_cmd, name))
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect('Credential "{}" does not exist'.format(name)) == 0
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
    password = utils.uuid4()

    become_password = utils.uuid4()
    new_become_password = utils.uuid4()
    cred_add_and_check(
        {
            "name": name,
            "username": username,
            "password": None,
            "become-password": None,
        },
        [("Password:", password), (BECOME_PASSWORD_INPUT, become_password)],
    )

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "become_method": '"sudo"',
                "become_user": '"root"',
                "become_password": MASKED_PASSWORD_OUTPUT,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
            }
        ),
    )

    qpc_cred_edit = pexpect.spawn(
        "{} -v cred edit --name={} --become-password".format(client_cmd, name)
    )
    assert qpc_cred_edit.expect(BECOME_PASSWORD_INPUT) == 0
    qpc_cred_edit.sendline(new_become_password)
    assert qpc_cred_edit.expect('Credential "{}" was updated'.format(name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "become_method": '"sudo"',
                "become_user": '"root"',
                "become_password": MASKED_PASSWORD_OUTPUT,
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
            }
        ),
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
    password = utils.uuid4()
    cred_add_and_check(
        {"name": name, "username": username, "password": None},
        [("Password:", password)],
    )

    name = utils.uuid4()
    qpc_cred_edit = pexpect.spawn(
        "{} -v cred edit --name={} --become-password".format(client_cmd, name)
    )
    assert qpc_cred_edit.expect('Credential "{}" does not exist'.format(name)) == 0
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

    qpc_cred_edit = pexpect.spawn("{} -v cred edit --name={} --password".format(client_cmd, name))
    qpc_cred_edit.logfile = BytesIO()
    assert qpc_cred_edit.expect('Credential "{}" does not exist'.format(name)) == 0
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
    password = utils.uuid4()

    cred_add_and_check(
        {"name": name, "username": username, "password": None}, [("Password", password)]
    )

    cred_show_and_check(
        {"name": name},
        generate_show_output(
            {
                "name": name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                "become_method": '"sudo"',
                "become_user": '"root"',
            }
        ),
    )

    qpc_cred_clear = pexpect.spawn("{} -v cred clear --name={}".format(client_cmd, name))
    assert qpc_cred_clear.expect('Credential "{}" was removed'.format(name)) == 0
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 0

    qpc_cred_show = pexpect.spawn("{} -v cred show --name={}".format(client_cmd, name))
    assert qpc_cred_show.expect('Credential "{}" does not exist'.format(name)) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()


def test_clear_with_source(isolated_filesystem, qpc_server_config):
    """Attempt to clear a credential being used by a source.

    :id: 66d84e9c-3124-11e8-b467-0ed5f89f718b
    :description: Create a credential and a source that utilizes the
        credential. Try to clear the credential entry by entering the --name
        of the credential which is associated with the source entry. After that
        remove the associated source entry and try to remove the credential
        again, it should now be removed.
    :steps:
        1) Run ``qpc cred add --name <name> --type <type> --username <username>
        --sshkeyfile <sshkeyfile>``
        2) Run ``qpc source add --name <name> --type <type> --cred <cred>
        --hosts <hosts>``
        3) Run ``qpc cred clear --name <name>`` (fails due to source)
        4) Run ``qpc source clear --name <name>``
        5) Run ``qpc cred clear --name <name>``
    :expectedresults: The credential is only removed after the source that is
        using it has been deleted.
    """
    cred_name = utils.uuid4()
    cred_type = "network"
    source_name = utils.uuid4()
    hosts = ["127.0.0.1"]
    username = utils.uuid4()
    password = utils.uuid4()

    cred_add_and_check(
        {
            "name": cred_name,
            "type": cred_type,
            "username": username,
            "password": None,
        },
        [("Password:", password)],
    )

    cred_show_and_check(
        {"name": cred_name},
        generate_show_output(
            {
                "name": cred_name,
                "password": MASKED_PASSWORD_OUTPUT,
                "username": username,
                "auth_type": "password",
                "become_method": '"sudo"',
                "become_user": '"root"',
            }
        ),
    )
    # create dependent source
    source_add_and_check({"name": source_name, "cred": [cred_name], "hosts": hosts})
    output = source_show({"name": source_name})
    output = json.loads(output)
    # try to delete credential
    qpc_cred_clear = pexpect.spawn("{} -v cred clear --name={}".format(client_cmd, cred_name))
    qpc_cred_clear.logfile = BytesIO()
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    assert (
        qpc_cred_clear.logfile.getvalue().strip().decode("utf-8")
        == "Error: Credential cannot be deleted because it is used by 1"
        " or more sources.\r\n"
        "sources: {'id': '%s', 'name': '%s'}\r\n"
        'Failed to remove credential "%s". '
        "For more information, see the server log file." % (output["id"], source_name, cred_name)
    )
    qpc_cred_clear.logfile.close()
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 1
    qpc_cred_clear.close()
    # delete the source using credential
    qpc_source_clear = pexpect.spawn("{} -v source clear --name={}".format(client_cmd, source_name))
    assert qpc_source_clear.expect('Source "{}" was removed'.format(source_name)) == 0
    assert qpc_source_clear.expect(pexpect.EOF) == 0
    qpc_source_clear.close()
    assert qpc_source_clear.exitstatus == 0
    # successfully remove credential
    qpc_cred_clear = pexpect.spawn("{} -v cred clear --name={}".format(client_cmd, cred_name))
    assert qpc_cred_clear.expect('Credential "{}" was removed'.format(cred_name)) == 0
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 0
    # try showing cred
    qpc_cred_show = pexpect.spawn("{} -v cred show --name={}".format(client_cmd, cred_name))
    assert qpc_cred_show.expect('Credential "{}" does not exist'.format(cred_name)) == 0
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
    qpc_cred_clear = pexpect.spawn("{} -v cred clear --name={}".format(client_cmd, name))
    qpc_cred_clear.logfile = BytesIO()
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    assert qpc_cred_clear.logfile.getvalue().strip().decode(
        "utf-8"
    ) == 'Credential "{}" was not found.'.format(name)
    qpc_cred_clear.logfile.close()
    qpc_cred_clear.close()
    assert qpc_cred_clear.exitstatus == 1


def test_clear_all(isolated_filesystem, qpc_server_config, cleaning_data_provider):
    """Clear all auth entries.

    :id: 16aa6914-e7ae-400f-b12b-6c9d218c4e0f
    :description: Clear multiple auth entries using the ``--all`` option.
    :steps: Run ``qpc cred clear --all``
    :expectedresults: All auth entries are removed.
    """
    expected_credential_count = random.randint(2, 3)
    for _ in range(expected_credential_count):
        options = {
            "name": utils.uuid4(),
            "username": utils.uuid4(),
            "password": None,
        }
        inputs = [
            ("Password:", utils.uuid4()),
        ]
        cred_add_and_check(options, inputs)

    output, exitstatus = pexpect.run(
        "{} -v cred clear --all".format(client_cmd),
        encoding="utf-8",
        withexitstatus=True,
    )
    assert (
        f"Successfully deleted {expected_credential_count} credentials. "
        "0 credentials could not be deleted." in output
    )
    assert exitstatus == 0

    output, exitstatus = pexpect.run(
        "{} -v cred list".format(client_cmd), encoding="utf8", withexitstatus=True
    )
    assert "No credentials exist yet." in output
    assert exitstatus == 0


@pytest.mark.upgrade_only
def test_edit_existing_credential_username(qpc_server_config, source_type):
    """Check that credential that existed before upgrade can be edited.

    We want to check all credential types, but the only field that is common
    for all of them is the name - and this is one field that CLI can not
    change. So we try to change username instead, but RHACS and OpenShift
    token do not have it.

    :id: 93dd6711-ef58-4370-9e4a-d427785a9bf9
    :description: Edit existing credential
    :steps:
        1) Select a credential of specified type
        2) Edit credential, changing the username
        3) Verify that credential was changed
        4) Edit credential again, restoring old username
    :expectedresults: Credential is modified and changes are saved.
    """
    new_username = utils.uuid4()

    output, _ = pexpect.run(
        "{} -v cred list --type {}".format(client_cmd, source_type),
        encoding="utf8",
        withexitstatus=True,
    )
    try:
        all_credentials = json.loads(output)
    except ValueError:
        pytest.skip("There are no credentials of this type")

    filtered_credentials = [cred for cred in all_credentials if cred.get("username")]
    if not filtered_credentials:
        pytest.skip("No credential with username")

    credential = random.choice(filtered_credentials)
    credential_name = credential.get("name")

    # Edit credential
    output, exitstatus = pexpect.run(
        "{} -v cred edit --name={} --username={}".format(client_cmd, credential_name, new_username),
        encoding="utf-8",
        withexitstatus=True,
    )
    assert f'Credential "{credential_name}" was updated' in output
    assert exitstatus == 0

    # Grab the new data, prepare both for comparison, compare
    output, exitstatus = pexpect.run(
        "{} -v cred show --name={}".format(client_cmd, credential_name),
        encoding="utf-8",
        withexitstatus=True,
    )
    updated_credential = json.loads(output)
    expected = credential.copy()
    expected["username"] = new_username
    expected.pop("updated_at", None)
    updated_credential.pop("updated_at", None)

    assert expected == updated_credential

    # Restore old username
    pexpect.run(
        "{} -v cred edit --name={} --username={}".format(
            client_cmd, credential_name, credential.get("username")
        )
    )
