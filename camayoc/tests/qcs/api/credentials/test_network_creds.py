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
import random
from pathlib import Path

from camayoc import api
from camayoc.qcs_models import Credential
from camayoc.utils import uuid4
from camayoc.tests.qcs.utils import assert_matches_server


def test_create_with_password(shared_client, cleanup):
    """Create a host credential with username and password.

    :id: d04e3e1b-c7f1-4cc2-a4a4-a3d3317f95ce
    :description: Create a host credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new host credential entry is created with the data.
    """
    cred = Credential(
        cred_type='network',
        client=shared_client,
        password=uuid4())
    cred.create()
    # add the credential to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)


def test_update_username(shared_client, cleanup):
    """Create a host credential and then update its username.

    :id: 73ed2ed5-e623-48ec-9ea6-153017464d9c
    :description: Create a host credential with password, then update its
        username.
    :steps:
        1) Create a host credential with a username and password.
        2) Update the host credential with a new username.
        3) Confirm host credential has been updated.
    :expectedresults: The host credential is updated.
    """
    cred = Credential(
        cred_type='network',
        client=shared_client,
        password=uuid4())
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)

    # give the cred a new username
    cred.username = uuid4()
    cred.update()
    assert_matches_server(cred)


def test_update_password_to_sshkeyfile(
        shared_client, cleanup, isolated_filesystem):
    """Create a host credential using password and switch it to use sshkey.

    :id: 6e557092-192b-4f75-babc-abc5774fe965
    :description: Create a host credential with password, then update it
        to use a sshkey.
    :steps:
        1) Create a host credential with a username and password.
        2) Update the host credential deleting password and adding sshkey.
        3) Confirm host credential has been updated.
    :expectedresults: The host credential is updated.
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
    """Create a host credential using password and switch it to use sshkey.

    :id: d24a54b5-3d8c-44e4-a0ae-61584a15b127
    :description: Create a host credential with a sshkey, then update it
        to use a password.
    :steps:
        1) Create a host credential with a username and sshkey.
        2) Update the host credential deleting sshkey and updating
           password.
        3) Confirm host credential has been updated.
    :expectedresults: The host credential is updated.
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
    cred.client.response_handler = api.echo_handler
    cred.password = uuid4()
    cred.ssh_keyfile = None
    cred.update()
    assert_matches_server(cred)


def test_negative_update_to_invalid(
        shared_client, cleanup, isolated_filesystem):
    """Attempt to update valid credential with invalid data.

    :id: c34ea917-ee36-4b93-8907-24a5f87bbed3
    :description: Create valid host credentials, then attempt to update to be
        invalid.
    :steps:
        1) Create valid credentials with passwords or sshkey.
        2) Update the host credentials:
            a) missing usernames
            b) using both password and sshkey
            c) missing both password and sshkey
    :expectedresults: Error codes are returned and the host credentials are
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
    # Try to update with username equals null
    old = cred.username
    cred.username = None
    response = cred.update()
    assert response.status_code == 400
    cred.username = old
    assert_matches_server(cred)

    # Try to update with both sshkeyfile and password
    cred.password = uuid4()
    response = cred.update()
    assert response.status_code == 400
    cred.password = None
    assert_matches_server(cred)

    # Try to update with both sshkeyfile and password missing
    old = cred.ssh_keyfile
    cred.ssh_keyfile = None
    response = cred.update()
    assert response.status_code == 400
    cred.ssh_keyfile = old
    assert_matches_server(cred)


def test_create_with_sshkey(
        shared_client, cleanup, isolated_filesystem):
    """Create a host credential with username and sshkey.

    :id: ab6fd574-2e9f-46b8-847d-17b23c19fdd2
    :description: Create a host credential with a user name and sshkey
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new host credential entry is created with the data.
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
    """Attempt to create a host credential with sshkey and password.

    The request should be met with a 4XX response.

    :id: 22a2ca65-5f9d-4c43-89ad-d7ab53223896
    :description: Create a host credential with username, sshkey, and password.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
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
    assert cred._id is None


def test_negative_create_no_name(cleanup):
    """Attempt to create a host credential missing a name.

    The request should be met with a 4XX response.

    :id: faf2d9fd-8b19-4bf7-b4a9-761da6de34e4
    :description: Create a host credential missing a name.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
    """
    client = api.Client(api.echo_handler)
    cred = Credential(
        cred_type='network',
        client=client,
        username='',
        password=uuid4(),
    )
    response = cred.create()
    assert response.status_code == 400
    assert cred._id is None


def test_negative_create_no_key_or_pass(cleanup):
    """Attempt to create a host credential missing both password and sshkey.

    The request should be met with a 4XX response.

    :id: 97a24094-3e9b-4eca-884e-3eda4e461ea1
    :description: Create a host credential missing both password and sshkey.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
    """
    client = api.Client(api.echo_handler)
    cred = Credential(cred_type='network', client=client)
    response = cred.create()
    assert response.status_code == 400
    assert cred._id is None


def test_read_all(shared_client, cleanup):
    """After created, retrieve all host credentials with GET to api.

    :id: fa05b857-5b01-4388-9226-8dfb5639c815
    :description: The API should return list with all host credentials created
        when a GET request is sent to the host credential endpoint.
    :steps:
        1) Create collection of host credentials, saving the information.
        2) Send GET request to host credential endpoint to get list of
           created host credentials.
        3) Confirm that all hosts are in the list.
    :expectedresults: All hosts are present in data returned by API.
    """
    creds = []
    for _ in range(random.randint(2, 5)):
        cred = Credential(
            cred_type='network',
            client=shared_client,
            password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        cleanup.append(cred)
        assert_matches_server(cred)
        creds.append(cred)

    remote_creds = Credential(cred_type='network', ).list().json()
    for local, remote in zip(creds, remote_creds):
        local.equivalent(remote)


def test_read_indv(shared_client, cleanup):
    """After created, retrieve each host credential with GET to api.

    :id: 4d381119-2dc3-42b6-9b41-e27307d61fcc
    :description: The API should a single host credential when a GET is made
        to the host credentials path and a host id is specified.
    :steps:
        1) Create collection of host credentials, saving the information.
        2) Send GET request to host credential endpoint with the host id
           specified.
        3) Confirm that each host is retrieved
    :expectedresults: All hosts are present in data returned by API.
    """
    creds = []
    for _ in range(random.randint(2, 5)):
        cred = Credential(
            cred_type='network',
            client=shared_client,
            password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        cleanup.append(cred)
        assert_matches_server(cred)
        creds.append(cred)

    for cred in creds:
        remote = Credential(cred_type='network', _id=cred._id).read().json()
        cred.equivalent(remote)


def test_delete(shared_client, cleanup):
    """After creating several host credentials, delete one.

    :id: e71b521c-59f9-483a-9063-1fbd5087c667
    :description: Test that we can delete an individual host credential by id
    :steps:
        1) Create collection of host credentials, saving the information.
        2) Send a DELETE request to destroy individual host credential
        3) Send GET request to host credential endpoint to get list of
           created host credentials.
        4) Confirm that all hosts are in the list except the deleted one.
        5) Repeat until all hosts are deleted.
    :expectedresults: All hosts are present in data returned by API except
        the deleted credential.
    """
    creds = []
    for _ in range(random.randint(2, 5)):
        cred = Credential(
            cred_type='network',
            client=shared_client,
            password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        cleanup.append(cred)
        assert_matches_server(cred)
        creds.append(cred)

    while creds:
        selected = random.choice(creds)
        cleanup.remove(selected)
        creds.remove(selected)
        selected.delete()

        for cred in creds:
            remote = Credential(_id=cred._id).read().json()
            cred.equivalent(remote)
