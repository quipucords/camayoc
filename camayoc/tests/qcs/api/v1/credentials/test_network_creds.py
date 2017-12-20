# coding=utf-8
"""Tests for Network source use cases of ``Credential`` API endpoint.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from pathlib import Path

import pytest

from camayoc import api
from camayoc.qcs_models import Credential
from camayoc.utils import uuid4
from camayoc.tests.qcs.utils import assert_matches_server


def test_update_password_to_sshkeyfile(
        shared_client, cleanup, isolated_filesystem):
    """Create a network credential using password and switch it to use sshkey.

    :id: 6e557092-192b-4f75-babc-abc5774fe965
    :description: Create a network credential with password, then update it
        to use a sshkey.
    :steps:
        1) Create a network credential with a username and password.
        2) Update the network credential deleting password and adding sshkey.
        3) Confirm network credential has been updated.
    :expectedresults: The network credential is updated.
    """
    cred = Credential(
        cred_type='network',
        client=shared_client,
        password=uuid4())
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)

    sshkeyfile = Path(uuid4())
    sshkeyfile.touch()

    cred.ssh_keyfile = str(sshkeyfile.resolve())
    cred.password = None
    cred.update()
    assert_matches_server(cred)


def test_update_sshkey_to_password(
        shared_client, cleanup, isolated_filesystem):
    """Create a network credential using password and switch it to use sshkey.

    :id: d24a54b5-3d8c-44e4-a0ae-61584a15b127
    :description: Create a network credential with a sshkey, then update it
        to use a password.
    :steps:
        1) Create a network credential with a username and sshkey.
        2) Update the network credential deleting sshkey and updating
           password.
        3) Confirm network credential has been updated.
    :expectedresults: The network credential is updated.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    cred = Credential(
        cred_type='network',
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)
    cred.client.response_handler = api.echo_handler
    cred.password = uuid4()
    cred.ssh_keyfile = None
    cred.update()
    assert_matches_server(cred)


def test_negative_update_to_invalid(
        shared_client, cleanup, isolated_filesystem):
    """Attempt to update valid credential with invalid data.

    :id: c34ea917-ee36-4b93-8907-24a5f87bbed3
    :description: Create valid network credentials, then attempt to update to
        be invalid.
    :steps:
        1) Create valid credentials with passwords or sshkey.
        2) Update the network credentials:
            a) using both password and sshkey
            b) missing both password and sshkey
    :expectedresults: Error codes are returned and the network credentials are
        not updated.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    cred = Credential(
        cred_type='network',
        client=shared_client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)

    cred.client = api.Client(api.echo_handler)

    # Try to update with both sshkeyfile and password
    cred.password = uuid4()
    response = cred.update()
    assert response.status_code == 400
    assert 'either a password or an ssh_keyfile, not both' in response.text
    cred.password = None
    assert_matches_server(cred)

    # Try to update with both sshkeyfile and password missing
    old = cred.ssh_keyfile
    del cred.ssh_keyfile
    response = cred.update()
    assert response.status_code == 400
    assert 'must have either a password or an ssh_keyfile' in response.text
    cred.ssh_keyfile = old
    assert_matches_server(cred)


def test_create_with_sshkey(
        shared_client, cleanup, isolated_filesystem):
    """Create a network credential with username and sshkey.

    :id: ab6fd574-2e9f-46b8-847d-17b23c19fdd2
    :description: Create a network credential with a user name and sshkey
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new network credential entry is created with the data.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    cred = Credential(
        cred_type='network',
        client=shared_client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)


def test_negative_create_key_and_pass(cleanup, isolated_filesystem):
    """Attempt to create a network credential with sshkey and password.

    The request should be met with a 4XX response.

    :id: 22a2ca65-5f9d-4c43-89ad-d7ab53223896
    :description: Create a network credential with username, sshkey, and
        password.
    :steps: Send POST with necessary data to the credential api endpoint.
    :expectedresults: Error is thrown and no new network credential is created.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    client = api.Client(api.echo_handler)
    cred = Credential(
        cred_type='network',
        client=client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
        password=uuid4(),
    )
    response = cred.create()
    assert response.status_code == 400
    assert 'either a password or an ssh_keyfile, not both' in response.text
    assert cred._id is None


@pytest.mark.skip
def test_create_sudo_password(cleanup, isolated_filesystem):
    """Create a network credential that has a sudo password.

    :id: e49e497d-abb7-4d6a-8366-3409e297062a
    :description: Create a network credential with username, password XOR
        sshkey, and a sudo password.
    :steps: Send a POST to the credential endpoint with data.
    :expectedresults: A new network credential is created.
    :caseautomation: notautomated
    """
    pass
