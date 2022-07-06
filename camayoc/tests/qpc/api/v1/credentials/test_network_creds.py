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
import os
from pathlib import Path

import pytest
import requests

from camayoc import api
from camayoc import utils
from camayoc.constants import QPC_BECOME_METHODS
from camayoc.qpc_models import Credential
from camayoc.tests.qpc.utils import assert_matches_server
from camayoc.utils import uuid4


@pytest.mark.ssh_keyfile_path
def test_update_password_to_sshkeyfile(shared_client, cleanup, isolated_filesystem):
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
    cred = Credential(cred_type="network", client=shared_client, password=uuid4())
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)

    sshkeyfile_name = utils.uuid4()
    tmp_dir = os.path.basename(os.getcwd())
    sshkeyfile = Path(sshkeyfile_name)
    sshkeyfile.touch()

    cred.ssh_keyfile = f"/sshkeys/{tmp_dir}/{sshkeyfile_name}"
    cred.password = None
    cred.update()
    assert_matches_server(cred)


@pytest.mark.ssh_keyfile_path
def test_update_sshkey_to_password(shared_client, cleanup, isolated_filesystem):
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
    sshkeyfile_name = utils.uuid4()
    tmp_dir = os.path.basename(os.getcwd())
    sshkeyfile = Path(sshkeyfile_name)
    sshkeyfile.touch()

    cred = Credential(cred_type="network", ssh_keyfile=f"/sshkeys/{tmp_dir}/{sshkeyfile_name}")
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)
    cred.client.response_handler = api.echo_handler
    cred.password = uuid4()
    cred.ssh_keyfile = None
    cred.update()
    assert_matches_server(cred)


@pytest.mark.ssh_keyfile_path
def test_negative_update_to_invalid(shared_client, cleanup, isolated_filesystem):
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
    sshkeyfile_name = utils.uuid4()
    tmp_dir = os.path.basename(os.getcwd())
    sshkeyfile = Path(sshkeyfile_name)
    sshkeyfile.touch()

    cred = Credential(
        cred_type="network",
        client=shared_client,
        ssh_keyfile=f"/sshkeys/{tmp_dir}/{sshkeyfile_name}",
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
    assert "either a password or an ssh_keyfile, not both" in response.text
    cred.password = None
    assert_matches_server(cred)

    # Try to update with both sshkeyfile and password missing
    old = cred.ssh_keyfile
    del cred.ssh_keyfile
    response = cred.update()
    assert response.status_code == 400
    assert "must have either a password or an ssh_keyfile" in response.text
    cred.ssh_keyfile = old
    assert_matches_server(cred)


@pytest.mark.ssh_keyfile_path
def test_create_with_sshkey(shared_client, cleanup, isolated_filesystem):
    """Create a network credential with username and sshkey.

    :id: ab6fd574-2e9f-46b8-847d-17b23c19fdd2
    :description: Create a network credential with a user name and sshkey
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new network credential entry is created with the data.
    """
    sshkeyfile_name = utils.uuid4()
    tmp_dir = os.path.basename(os.getcwd())
    sshkeyfile = Path(sshkeyfile_name)
    sshkeyfile.touch()

    cred = Credential(
        cred_type="network",
        client=shared_client,
        ssh_keyfile=f"/sshkeys/{tmp_dir}/{sshkeyfile_name}",
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
        cred_type="network",
        client=client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
        password=uuid4(),
    )
    response = cred.create()
    assert response.status_code == 400
    assert "either a password or an ssh_keyfile, not both" in response.text
    assert cred._id is None


@pytest.mark.parametrize("method", QPC_BECOME_METHODS)
def test_create_become_method(cleanup, shared_client, method):
    """Create a network credential that uses become options.

    :id: e49e497d-abb7-4d6a-8366-3409e297062a
    :description: Create a network credential with username, password
        and uses a become method.
    :steps: Send a POST to the credential endpoint with data.
    :expectedresults: A new network credential is created.
    """
    cred = Credential(
        cred_type="network",
        client=shared_client,
        password=uuid4(),
        become_method=method,
        become_password=uuid4(),
        become_user=uuid4(),
    )
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)


@pytest.mark.parametrize("invalid_method", ["not-a-method", 86])
def test_negative_invalid_become_method(cleanup, shared_client, invalid_method):
    """Attempt to create a network credential with unsupported become options.

    :id: f05f2ea8-ae9f-4bad-a76f-5246128400d9
    :description: Submit an otherwise well formed request to create a network
        credential with a become method, but provide a become method that is
        not supported.
    :steps: Send a POST to the credential endpoint that is well formed except
        contains a become method that the server does not know how to use.
    :expectedresults: No new credential is created.
    """
    cred = Credential(
        cred_type="network",
        client=shared_client,
        password=uuid4(),
        become_method=invalid_method,
        become_password=uuid4(),
        become_user=uuid4(),
    )
    with pytest.raises(requests.HTTPError):
        cred.create()
        cleanup.append(cred)
