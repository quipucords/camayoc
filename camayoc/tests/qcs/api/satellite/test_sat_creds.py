# coding=utf-8
"""Tests for Satellite use cases of ``Credentials`` API endpoint.

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
    """Create a Satellite credential with username and password.

    :id: a8ec480a-a9fd-4042-ab23-c363f07af33f
    :description: Create a Satellite credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new Satellite credential entry is created with the
        data.
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('field', ['username', 'password'])
def test_update_field(field, shared_client, cleanup):
    """Create a Satellite credential and then update its username or password.

    :id: 1a5790a4-9dc1-4ccb-bec5-5753bd487484
    :description: Create a Satellite credential with password, then update its
        username.
    :steps:
        1) Create a Satellite credential with a username and password.
        2) Update the Satellite credential with a new username.
        3) Confirm Satellite credential has been updated.
    :expectedresults: The Satellite credential is updated.
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('cred_type', ['vcenter', 'network'])
def test_negative_update_to_other_type(
    shared_client,
    cleanup,
    isolated_filesystem,
    cred_type
):
    """Attempt to update valid credential to be another type.

    :id: 6ad285a0-7aa9-4ff7-8749-de73b33090c4
    :description: Create a valid Satellite credential, then attempt to update
        to be another type.
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

    :id: a62d171d-2cec-473c-8bec-76c6ca022fac
    :description: Create a credential missing a field.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new credential is created.
    """
    pass


@pytest.mark.skip
def test_read_all(shared_client, cleanup):
    """After created, retrieve Satellite credentials with GET to api.

    :id: d41d2df4-d304-4b09-8970-62c06bb5724d
    :description: The API should return list with all credentials created
        when a GET request is sent to the credential endpoint.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint to get list of
           created Satellite credentials.
        3) Confirm that all credentials are in the list.
    :expectedresults: All credentials are present in data returned by API.
    """
    pass


@pytest.mark.skip
def test_read_indv(shared_client, cleanup):
    """After created, retrieve each credential with GET to api.

    :id: 2afd9de7-c99a-4377-b42f-a5bf130c628c
    :description: The API should a single credential when a GET is made
        to the Satellite credentials path and a credential id is specified.
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send GET request to credential endpoint with the Satellite id
           specified.
        3) Confirm that each Satellite is retrieved
    :expectedresults: All credentials are present in data returned by API.
    """
    pass


@pytest.mark.skip
def test_delete(shared_client, cleanup):
    """After creating several credentials, delete one.

    :id: c9a96fc4-09cc-4995-a64d-54d1396603bd
    :description: Test that we can delete an individual credential by id
    :steps:
        1) Create collection of credentials, saving the information.
        2) Send a DELETE request to destroy individual Satellite credential
        3) Send GET request to Satellite credential endpoint to get list of
           created Satellite credentials.
        4) Confirm that all credentials are in the list except the deleted one.
        5) Repeat until all credentials are deleted.
    :expectedresults: All credentials are present in data returned by API
        except the deleted credential.
    """
    pass
