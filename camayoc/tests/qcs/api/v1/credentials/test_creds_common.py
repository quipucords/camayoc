# coding=utf-8
"""Tests for the ``Credential`` API endpoint.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import random

import pytest

from camayoc import api
from camayoc.constants import QCS_SOURCE_TYPES
from camayoc.qcs_models import Credential
from camayoc.utils import uuid4
from camayoc.tests.qcs.utils import assert_matches_server


@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_create_with_password(cred_type, shared_client, cleanup):
    """Create a credential with username and password.

    :id: bcc6a15f-a5b5-4939-9602-e5bccf4a75ca
    :description: Create a credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new credential entry is created with the data.
    """
    cred = Credential(
        cred_type=cred_type,
        client=shared_client,
        password=uuid4())
    cred.create()
    # add the credential to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)


@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('field', ['name', 'username', 'password'])
def test_update(cred_type, field, shared_client, cleanup):
    """Create a credential and then update its name, username or password.

    :id: 73ed2ed5-e623-48ec-9ea6-153017464d9c
    :description: Create a credential with password, then update its
        name, username or password.
    :steps:
        1) Create a credential with a username and password.
        2) Update the credential with a new name, username or password.
        3) Confirm credential has been updated.
    :expectedresults: The credential is updated.
    """
    cred = Credential(
        cred_type=cred_type,
        client=shared_client,
        password=uuid4())
    cred.create()
    # add the id to the list to destroy after the test is done
    cleanup.append(cred)
    assert_matches_server(cred)

    # give the cred a new value for the field
    setattr(cred, field, uuid4())
    cred.update()
    assert_matches_server(cred)


@pytest.mark.skip
@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_negative_update_to_invalid(
    cred_type,
    shared_client,
    cleanup,
):
    """Attempt to update valid credential with invalid data.

    :id: d3002d47-daee-4fcc-ac7c-477738ffc447
    :description: Create valid credentials, then attempt to update to be
        invalid.
    :steps:
        1) Create valid credentials with passwords.
        2) Update the credentials:
            a) missing username
            c) missing password
    :expectedresults: Error codes are returned and the credentials are
        not updated.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.parametrize('field', ['name', 'username', 'password'])
@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_negative_create_missing_field(cred_type, field, cleanup):
    """Attempt to create a credential missing a name.

    The request should be met with a 4XX response.

    :id: faf2d9fd-8b19-4bf7-b4a9-761da6de34e4
    :description: Create a credential missing a name, username, or password.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new credential is created.
    """
    client = api.Client(api.echo_handler)
    cred = Credential(
        cred_type=cred_type,
        client=client,
        username=uuid4(),
        password=uuid4(),
        name=uuid4(),
    )
    delattr(cred, field)
    response = cred.create()
    assert response.status_code == 400
    assert cred._id is None


@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_list(cred_type, shared_client, cleanup):
    """After created, retrieve all credentials with GET to api.

    :id: fa05b857-5b01-4388-9226-8dfb5639c815
    :description: The API should return list with all credentials created
        when a GET request is sent to the credential endpoint.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint to get list of
           created credentials.
        3) Confirm that all creds are in the list.
    :expectedresults: All creds are present in the list returned from the
        credentials endpoint when a GET request is sent.
    """
    local_creds = []
    for _ in range(random.randint(2, 7)):
        cred = Credential(
            cred_type=cred_type,
            client=shared_client,
            password=uuid4())
        cred.create()
        cleanup.append(cred)
        assert_matches_server(cred)
        local_creds.append(cred)

    remote_creds = Credential().list().json()
    for local in local_creds:
        match_exists = False
        for remote in remote_creds:
            if remote.get('id') == local._id:
                match_exists = True
                assert local.equivalent(remote)
        assert match_exists


@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_read(cred_type, shared_client, cleanup):
    """After created, retrieve each credential with GET to api.

    :id: 4d381119-2dc3-42b6-9b41-e27307d61fcc
    :description: The API should a single credential when a GET is made
        to the credentials path and a id is specified.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint with the id
           specified.
        3) Confirm that each is retrieved
    :expectedresults: Each credential can be read individually and has correct
        data returned when it is queried.
    """
    creds = []
    for _ in range(random.randint(2, 5)):
        cred = Credential(
            cred_type=cred_type,
            client=shared_client,
            password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        cleanup.append(cred)

        # assert_matches_server reads the credential on the server
        assert_matches_server(cred)
        creds.append(cred)


@pytest.mark.parametrize('cred_type', QCS_SOURCE_TYPES)
def test_delete(cred_type, shared_client, cleanup):
    """After creating several credentials, delete one.

    :id: e71b521c-59f9-483a-9063-1fbd5087c667
    :description: Test that we can delete an individual credential by id
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send a DELETE request to destroy individual credential
        3) Send GET request to credential endpoint to get list of
           created credentials.
        4) Confirm that all credentials are in the list except the deleted
           one.
        5) Repeat until all credentials are deleted.
    :expectedresults: All credentials are present in data returned by API
        except the deleted credential.
    """
    creds = []
    for _ in range(random.randint(2, 5)):
        cred = Credential(
            cred_type=cred_type,
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


@pytest.mark.skip
def test_negative_update_to_other_type(
    shared_client,
    cleanup,
    cred_type
):
    """Attempt to update valid credential to be another type.

    :id: 6ad285a0-7aa9-4ff7-8749-de73b33090c4
    :description: Create a valid credential of one type, then attempt to update
        to be another type.
    :steps:
        1) Create valid credential with password
        2) Update the credential with another type.
    :expectedresults: Error codes are returned and the credential is
        not updated.
    :caseautomation: notautomated
    """
    pass
