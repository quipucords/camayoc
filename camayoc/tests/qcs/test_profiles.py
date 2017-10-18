# coding=utf-8
"""Tests for ``Network Profile`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: sonar
:testtype: functional
:upstream: yes
"""

import pytest

from uuid import uuid4

from camayoc.qcs_models import HostCredential
from camayoc.qcs_models import NetworkProfile
from camayoc.tests.qcs.utils import assert_matches_server

CREATE_DATA = ['localhost', '127.0.0.1']


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_create(shared_client, cleanup, scan_host):
    """Create a Network Profile using a single credential.

    :id: db459fc2-d34c-45cf-915a-1535406a9320
    :description: Create network profile of single host and credential
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
    :expectedresults: A new network profile entry is created with the data.
    """
    cred = HostCredential(client=shared_client, password=str(uuid4()))
    cred.create()
    profile = NetworkProfile(
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    profile.create()
    # add the ids to the lists to destroy after the test is done
    cleanup.extend([cred, profile])

    assert_matches_server(profile)


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update(shared_client, cleanup, scan_host):
    """Create a Network Profile and then update it.

    :id: d57d8481-54e3-4d9a-b330-80edc9364f37
    :description: Create network profile of single host and credential
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
        3) Add a host and a new credential and send and PUT to the server with
           the data
    :expectedresults: The newtork profile entry is created and updated.
    """
    cred = HostCredential(client=shared_client, password=str(uuid4()))
    cred.create()
    profile = NetworkProfile(
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    profile.create()
    assert_matches_server(profile)
    profile.hosts.append('0.0.0.0')
    cred2 = HostCredential(password=str(uuid4()))
    cred2.create()
    profile.credentials.append(cred2._id)
    profile.update()
    cleanup.extend([cred, cred2, profile])
    assert_matches_server(profile)


@pytest.mark.skip
def test_negative_update_to_invalid(cleanup):
    """Attempt to update valid profile with invalid data.

    :id: 79954c63-608c-46b3-81eb-e2a1e984473e
    :description: Create valid network profile, and then attempt to update
        it with invalid data.
    :steps:
        1) Create valid credential and profile
        2) Update the profile with:
            a) invalid credentials
            b) Remove all credentials
            c) Remove all hosts
            d) An invalid host
            e) Non-existent fields
    :expectedresults: Error codes are returned and the profile is not updated.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_negative_create_missing_data(cleanup):
    """Attempt to create a profile missing various data.

    The requests should be met with a 4XX response.

    :id: 4b176997-0be2-4bd8-81fd-8b4ef5045382
    :description: Attempt to create profiles missing required data.
    :steps: Attempt to create a profile missing:
            a) a name
            b) hosts
            c) credential id's
    :expectedresults: Error is thrown and no new profile is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_negative_create_invalid_data(cleanup):
    """Attempt to create a profile missing various data.

    The requests should be met with a 4XX response.

    :id: e8754fd4-8d03-4899-bfde-0fc587d78ae1
    :description: Attempt to create profiles missing required data.
    :steps: Attempt to create a profile with invalid:
            a) name
            b) hosts
            c) credential id's
    :expectedresults: Error is thrown and no new profile is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_read_all(cleanup):
    """After created, retrieve all network profiles with GET to api.

    :id: e708362c-a289-46f1-ad05-724e3e4383d5
    :description: The API should return list with all profiles created
        when a GET request is sent to the network profiles endpoint.
    :steps:
        1) Create collection of profiles, saving the information.
        2) Send GET request to network profile endpoint to get list of
           created network profiles
        3) Confirm that all profiles are in the list.
    :expectedresults: All profiles are present in data returned by API.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_delete(cleanup):
    """After creating several network profiles, delete one.

    :id: 24d811b1-655d-4278-ab9f-64ca46a7121b
    :description: Test that we can delete an individual network profile by id
    :steps:
        1) Create collection of network profiles, saving the information.
        2) Send a DELETE request to destroy individual profile
        3) Send GET request to network profile endpoint to get list of
           created profiles.
        4) Confirm that all profiles are in the list except the deleted one.
        5) Repeat until all profiles are deleted.
    :expectedresults: All profiles are present in data returned by API except
        the deleted profle.
    :caseautomation: notautomated
    """
    pass
