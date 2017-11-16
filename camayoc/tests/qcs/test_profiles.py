# coding=utf-8
"""Tests for ``Network Profile`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import copy
import random

import pytest

from camayoc import api
from camayoc.utils import uuid4
from camayoc.qcs_models import HostCredential
from camayoc.qcs_models import NetworkProfile
from camayoc.tests.qcs.utils import (
    assert_matches_server,
    assert_profile_update_fails,
    gen_valid_profile,
)

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
    cred = HostCredential(client=shared_client, password=uuid4())
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
    cred = HostCredential(client=shared_client, password=uuid4())
    cred.create()
    cleanup.append(cred)
    profile = NetworkProfile(
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    profile.create()
    cleanup.append(profile)
    assert_matches_server(profile)
    profile.hosts.append('0.0.0.0')
    cred2 = HostCredential(password=uuid4())
    cred2.create()
    cleanup.append(cred2)
    profile.credentials.append(cred2._id)
    profile.update()
    assert_matches_server(profile)


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update_bad_credential(scan_host, cleanup):
    """Attempt to update valid profile with invalid data.

    :id: 79954c63-608c-46b3-81eb-e2a1e984473e
    :description: Create valid network profile, and then attempt to update
        it with an invalid credential.
    :steps:
        1) Create valid credential and profile
        2) Update the profile with invalid credentials
    :expectedresults: Error codes are returned and the profile is not updated.
    """
    profile = gen_valid_profile(cleanup, scan_host)
    original_data = copy.deepcopy(profile.fields())

    # Case "a" add credential that doesnt exist
    # The server never assigns negative values
    profile.credentials.append(-1)
    assert_profile_update_fails(original_data, profile)


@pytest.mark.parametrize('field', ['credentials', 'hosts'])
def test_update_remove_field(cleanup, field):
    """Attempt to update valid profile with either no hosts or no credentials.

    :id: 49feb858-319f-4f77-b330-65426dfd1734
    :description: Create valid network profile, and then attempt to update
        it to have either no credentials or no hosts.
    :steps:
        1) Create valid credential and profile
        2) Update the profile with no credentials or no hosts
    :expectedresults: Error codes are returned and the profile is not updated.
    """
    profile = gen_valid_profile(cleanup, 'localhost')
    # we have to use deep copy because these are nested dictionaries
    original_data = copy.deepcopy(profile.fields())
    # Case "b" update to have no credentials
    setattr(profile, field, [])
    assert_profile_update_fails(original_data, profile)


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update_with_bad_host(scan_host, cleanup):
    """Attempt to update valid profile with an invalid host.

    :id: 26176135-b147-46bc-b0b5-57d5bc515b72
    :description: Create valid network profile, and then attempt to update
        it with invalid hostname.
    :steps:
        1) Create valid credential and profile
        2) Update the profile with an invalid host
    :expectedresults: Error codes are returned and the profile is not updated.
    """
    profile = gen_valid_profile(cleanup, scan_host)
    original_data = copy.deepcopy(profile.fields())
    # Case "d" test updating profile with bad host
    profile.hosts.append('*invalid!!host&*')
    assert_profile_update_fails(original_data, profile)


@pytest.mark.parametrize(
    'field',
    ['name', 'hosts', 'credentials'],
    ids=['name', 'hosts', 'credentials']
)
def test_negative_create_missing_data(cleanup, shared_client, field):
    """Attempt to create a profile missing various data.

    The requests should be met with a 4XX response.

    :id: 4b176997-0be2-4bd8-81fd-8b4ef5045382
    :description: Attempt to create profiles missing required data.
    :steps: Attempt to create a profile missing:
            a) a name
            b) hosts
            c) credential id's
    :expectedresults: Error is thrown and no new profile is created.
    """
    cred = HostCredential(client=shared_client, password=uuid4())
    cred.create()
    cleanup.append(cred)
    profile = NetworkProfile(
        client=api.Client(response_handler=api.echo_handler),
        hosts=['localhost'],
        credential_ids=[cred._id],
    )

    # remove field from payload
    delattr(profile, field)
    create_response = profile.create()
    assert create_response.status_code == 400


@pytest.mark.parametrize('data',
                         [  # bad credential
                             {'hosts': ['localhost'],
                              'credential_ids': [-1],
                                 'name': uuid4()},
                             # bad host name
                             {'hosts': ['*invalidhostname*'],
                                 'credential_ids': None, 'name': uuid4()},
                             # bad name
                             {'hosts': ['localhost'],
                                 'credential_ids': None, 'name': ''},
                         ],
                         ids=['bad-credential',
                              'bad-hostname',
                              'bad-name'])
def test_negative_create_invalid_data(
        cleanup,
        shared_client,
        data):
    """Attempt to create a profile with invalid data.

    The requests should be met with a 4XX response.

    :id: e8754fd4-8d03-4899-bfde-0fc587d78ae1
    :description: Attempt to create profiles missing required data.
    :steps: Attempt to create a profile with invalid:
        a) creds
        b) host
        c) name
    :expectedresults: Error is thrown and no new profile is created.
    """
    cred = HostCredential(client=shared_client, password=uuid4())
    cred.create()
    cleanup.append(cred)
    data['credential_ids'] = cred._id if not data['credential_ids'] else [-1]
    profile = NetworkProfile(
        client=api.Client(response_handler=api.echo_handler),
        # unpack parametrized arguments
        **data
    )
    create_response = profile.create()
    assert create_response.status_code == 400


def test_read_all(cleanup, shared_client):
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
    """
    created_profs = []
    for _ in range(random.randint(2, 20)):
        # gen_valid_profs will take care of cleanup
        created_profs.append(gen_valid_profile(cleanup, 'localhost'))
    server_profs = NetworkProfile().list().json()
    for sp in server_profs:
        for i, cp in enumerate(created_profs):
            if sp['id'] == cp.fields()['id'] and cp.equivalent(sp):
                created_profs.remove(cp)
    # if we found everything we created, then the list should be empty
    assert len(created_profs) == 0


def test_delete(cleanup, shared_client):
    """After creating several network profiles, delete one.

    :id: 24d811b1-655d-4278-ab9f-64ca46a7121b
    :description: Test that we can delete an individual network profile by id
    :steps:
        1) Create collection of network profiles, saving the information.
        2) Send a DELETE request to destroy individual profile
        3) Confirm that all profiles are on the server except the deleted one.
        4) Repeat until all profiles are deleted.
    :expectedresults: All profiles are present on the server except the
        deleted profile.
    """
    created_profs = []
    num_profs = random.randint(2, 20)
    echo_client = api.Client(response_handler=api.echo_handler)
    for i in range(num_profs):
        # gen_valid_profs will take care of cleanup
        created_profs.append(gen_valid_profile(cleanup, 'localhost'))
    for i in range(num_profs):
        delete_prof = created_profs.pop()
        delete_prof.delete()
        delete_prof.client = echo_client
        delete_response = delete_prof.read()
        assert delete_response.status_code == 404
        for p in created_profs:
            assert_matches_server(p)
