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
import re

import pytest

from camayoc import api
from camayoc.constants import QPC_SOURCE_TYPES
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Source
from camayoc.tests.qpc.utils import assert_matches_server
from camayoc.utils import uuid4


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_create_with_password(cred_type, shared_client, data_provider):
    """Create a credential with username and password.

    :id: bcc6a15f-a5b5-4939-9602-e5bccf4a75ca
    :description: Create a credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new credential entry is created with the data.
    """
    cred = Credential(cred_type=cred_type, client=shared_client, password=uuid4())
    cred.create()
    # add the credential to the list to destroy after the test is done
    data_provider.mark_for_cleanup(cred)
    assert_matches_server(cred)


def test_create_with_token(shared_client, data_provider):
    """Create a credential with token.

    :id: 525096c3-d492-4231-988b-4491009c23b2
    :description: Create a credential with an authentication token
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new credential entry is created with the data.
    """
    cred = Credential(cred_type="openshift", client=shared_client, token=uuid4())
    cred.create()
    data_provider.mark_for_cleanup(cred)
    assert_matches_server(cred)


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
@pytest.mark.parametrize("field", ["name", "username", "password"])
def test_update(cred_type, field, shared_client, data_provider):
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
    cred = Credential(cred_type=cred_type, client=shared_client, password=uuid4())
    cred.create()
    # add the id to the list to destroy after the test is done
    data_provider.mark_for_cleanup(cred)
    assert_matches_server(cred)

    # give the cred a new value for the field
    setattr(cred, field, uuid4())
    cred.update()
    assert_matches_server(cred)


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_negative_update_to_invalid(cred_type, shared_client, data_provider):
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


@pytest.mark.parametrize("field", ["name", "username", "password"])
@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_negative_create_missing_field(cred_type, field, data_provider):
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


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_list(cred_type, shared_client, data_provider):
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
        cred = Credential(cred_type=cred_type, client=shared_client, password=uuid4())
        cred.create()
        data_provider.mark_for_cleanup(cred)
        assert_matches_server(cred)
        local_creds.append(cred)

    this_page = Credential().list().json()
    matches = 0
    while this_page:
        remote_creds = this_page["results"]
        for local in local_creds:
            for remote in remote_creds:
                if remote.get("id") == local._id:
                    if local.equivalent(remote):
                        matches += 1
        next_page = this_page.get("next")
        if next_page:
            # have to strip off host information from url
            next_page = re.sub(r".*/api", "/api", next_page)
            this_page = shared_client.get(next_page).json()
        else:
            break
    assert matches == len(local_creds)


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_read(cred_type, shared_client, data_provider):
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
        cred = Credential(cred_type=cred_type, client=shared_client, password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        data_provider.mark_for_cleanup(cred)

        # assert_matches_server reads the credential on the server
        assert_matches_server(cred)
        creds.append(cred)


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_delete_basic(cred_type, shared_client, data_provider):
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
        cred = Credential(cred_type=cred_type, client=shared_client, password=uuid4())
        cred.create()
        # add the credential to the list to destroy after the test is done
        data_provider.mark_for_cleanup(cred)
        assert_matches_server(cred)
        creds.append(cred)

    while creds:
        selected = random.choice(creds)
        creds.remove(selected)
        selected.delete()

        for cred in creds:
            remote = Credential(_id=cred._id).read().json()
            cred.equivalent(remote)


@pytest.mark.parametrize("obj_type", QPC_SOURCE_TYPES)
def test_delete_with_dependencies(obj_type, shared_client, data_provider):
    """We should not be allowed to delete a credential if souces depend on it.

    :id: cd88325e-d3e3-49a8-b39b-e0e7dffb0d92
    :description: Test that we can delete a credential only when it has no
        dependent sources.
    :steps:
        1) Create a credential.
        2) Create multiple sources that depend on it.
        3) Attempt to delete the credential.
        4) Assert that this fails.
        5) Delete the sources or replace the credential.
        6) Now attempt to delete the credential.
        7) Assert that this succeeds.
    :expectedresults: We cannot delete a credential until no sources depend
        on it.
    """
    cred = Credential(cred_type=obj_type, client=shared_client, password=uuid4())
    cred.create()
    data_provider.mark_for_cleanup(cred)
    srcs = []
    for _ in range(random.randint(3, 6)):
        src = Source(credential_ids=[cred._id], source_type=obj_type, hosts=["localhost"])
        src.create()
        data_provider.mark_for_cleanup(src)
        srcs.append(src)

    echo_client = api.Client(api.echo_handler)
    cred.client = echo_client
    del_response = cred.delete()
    assert del_response.status_code == 400
    assert "sources" in del_response.json().keys()
    cred.client = shared_client

    for i, src in enumerate(srcs):
        if i % 2 == 0:
            src.delete()
        else:
            new_cred = Credential(cred_type=obj_type, client=shared_client, password=uuid4())
            new_cred.create()
            data_provider.mark_for_cleanup(new_cred)
            src.credentials = [new_cred._id]
            src.update()

    # now we should be able to delete the credential
    cred.delete()


@pytest.mark.parametrize("cred_type", QPC_SOURCE_TYPES)
def test_negative_update_to_other_type(shared_client, data_provider, cred_type):
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
