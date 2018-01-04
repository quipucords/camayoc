# coding=utf-8
"""Tests for VCenter use cases of ``Credentials`` API endpoint.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""


import pytest


@pytest.mark.skip
def test_create(shared_client, cleanup):
    """Create a vcenter credential with username and password.

    :id: 987b9947-3cb1-445c-b2c1-5d5e48c4a34b
    :description: Create a vcenter credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new vcenter credential entry is created with the data.
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('field', ['username', 'password'])
def test_update_field(field, shared_client, cleanup):
    """Create a VCenter credential and then update its username or password.

    :id: 01b37998-e79c-4f5f-96a8-77c5142ff715
    :description: Create a vcenter credential with password, then update its
        username.
    :steps:
        1) Create a vcenter credential with a username and password.
        2) Update the vcenter credential with a new username.
        3) Confirm vcenter credential has been updated.
    :expectedresults: The vcenter credential is updated.
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('cred_type', ['satellite', 'network'])
def test_negative_update_to_other_type(
    shared_client,
    cleanup,
    isolated_filesystem,
    cred_type
):
    """Attempt to update valid credential to be other type.

    :id: d664894b-6e2f-4e72-a8a5-e888213ccb4c
    :description: Create a valid vcenter credential, then attempt to update to
        be another type.
    :steps:
        1) Create valid credential with password
        2) Update the credential with another type.
    :expectedresults: Error codes are returned and the credential is
        not updated.
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('field', ['username', 'password'])
def test_negative_missing_field(field, cleanup):
    """Attempt to create a credential missing a required field.

    The request should be met with a 4XX response.

    :id: 7c5ac362-2d3d-4371-bae8-84d2602c7bfb
    :description: Create a credential missing a field.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new credential is created.
    """
    pass


@pytest.mark.skip
def test_read_all(shared_client, cleanup):
    """After created, retrieve vcenter credentials with GET to api.

    :id: 66e9b6ac-b18f-4af1-8e15-7f0f1cd7f5fa
    :description: The API should return list with all credentials created
        when a GET request is sent to the credential endpoint.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint to get list of
           created vcenter credentials.
        3) Confirm that all credentials are in the list.
    :expectedresults: All credentials are present in data returned by API.
    """
    pass


@pytest.mark.skip
def test_read_indv(shared_client, cleanup):
    """After created, retrieve each credential with GET to api.

    :id: 3af796d0-4e43-4de3-af33-b388e9e40c36
    :description: The API should a single credential when a GET is made
        to the vcenter credentials path and a credential id is specified.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint with the vcenter id
           specified.
        3) Confirm that each vcenter is retrieved
    :expectedresults: All credentials are present in data returned by API.
    """
    pass


@pytest.mark.skip
def test_delete(shared_client, cleanup):
    """After creating several credentials, delete one.

    :id: 2217f951-a896-43c8-b2a1-46c410ac9d9f
    :description: Test that we can delete an individual credential by id
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send a DELETE request to destroy individual vcenter credential
        3) Send GET request to vcenter credential endpoint to get list of
           created vcenter credentials.
        4) Confirm that all credentials are in the list except the deleted one.
        5) Repeat until all credentials are deleted.
    :expectedresults: All credentials are present in data returned by API
        except the deleted credential.
    """
    pass
