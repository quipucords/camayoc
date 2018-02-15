# coding=utf-8
"""Tests for ``Source`` API endpoint for quipucords server.

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
from camayoc.constants import QCS_SOURCE_TYPES
from camayoc.utils import uuid4
from camayoc.qcs_models import Credential, Source
from camayoc.tests.qcs.utils import (
    assert_matches_server,
    assert_source_update_fails,
    gen_valid_source,
)

CREATE_DATA = ['localhost', '127.0.0.1', 'example.com']


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_create(shared_client, cleanup, scan_host, src_type):
    """Create a Source using a single credential.

    :id: db459fc2-d34c-45cf-915a-1535406a9320
    :description: Create {network, vcenter} source of single host and
        credential. Any valid IPv4 or dns name should be allowed to create a
        source.
    :steps:
        1) Create host credential
        2) Send POST with data to create the source using the credential to
           the source endpoint.
    :expectedresults: A new  source entry is created with the data.
    """
    cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4()
    )
    cred.create()
    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    src.create()
    # add the ids to the lists to destroy after the test is done
    cleanup.extend([cred, src])

    assert_matches_server(src)


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update(shared_client, cleanup, scan_host, src_type):
    """Create a {network, vcenter} source and then update it.

    :id: 900dda70-6208-44f5-b64d-f6ca4db7dfa4
    :description: Create {network, vcenter} source of single host and
        credential
    :steps:
        1) Create host credential
        2) Send POST with data to create {network, vcenter} source using the
           host credential to the source endpoint.
        3) Add a host and a new credential and send and PUT to the server with
           the data
    :expectedresults: The source entry is created and updated.
    """
    cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4()
    )
    cred.create()
    cleanup.append(cred)
    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    src.create()
    cleanup.append(src)
    assert_matches_server(src)
    src.hosts = ['example.com']
    cred2 = Credential(cred_type=src_type, password=uuid4())
    cred2.create()
    cleanup.append(cred2)
    src.credentials = [cred2._id]
    src.update()
    assert_matches_server(src)


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update_bad_credential(src_type, scan_host, cleanup):
    """Attempt to update valid source with invalid data.

    :id: 79954c63-608c-46b3-81eb-e2a1e984473e
    :description: Create valid {network, vcenter} source, and then attempt to
        update it with an invalid credential.
    :steps:
        1) Create valid credential and source
        2) Update the source with invalid credentials
    :expectedresults: Error codes are returned and the source is not updated.
    """
    src = gen_valid_source(cleanup, src_type, scan_host)
    original_data = copy.deepcopy(src.fields())

    # Case "a" add credential that doesnt exist
    # The server never assigns negative values
    src.credentials = [-1]
    assert_source_update_fails(original_data, src)


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('field', ['credentials', 'hosts'])
def test_update_remove_field(src_type, cleanup, field):
    """Attempt to update valid source with either no hosts or no credentials.

    :id: 49feb858-319f-4f77-b330-65426dfd1734
    :description: Create valid {network, vcenter} source, and then attempt to
        update it to have either no credentials or no hosts.
    :steps:
        1) Create valid credential and source
        2) Update the source with no credentials or no hosts
    :expectedresults: Error codes are returned and the source is not updated.
    """
    src = gen_valid_source(cleanup, src_type, 'localhost')
    # we have to use deep copy because these are nested dictionaries
    original_data = copy.deepcopy(src.fields())
    setattr(src, field, [])
    assert_source_update_fails(original_data, src)


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_update_with_bad_host(src_type, scan_host, cleanup):
    """Attempt to update valid source with an invalid host.

    :id: 26176135-b147-46bc-b0b5-57d5bc515b72
    :description: Create valid {network, vcenter} source, and then attempt to
        update it with invalid hostname.
    :steps:
        1) Create valid credential and source
        2) Update the source with an invalid host
    :expectedresults: Error codes are returned and the source is not updated.
    """
    src = gen_valid_source(cleanup, src_type, scan_host)
    original_data = copy.deepcopy(src.fields())
    # Test updating source with bad host
    src.hosts = ['*invalid!!host&*']
    assert_source_update_fails(original_data, src)


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
@pytest.mark.parametrize(
    'field',
    ['name', 'hosts', 'credentials'],
    ids=['name', 'hosts', 'credentials']
)
def test_negative_create_missing_data(src_type, cleanup, shared_client, field):
    """Attempt to create a source missing various data.

    The requests should be met with a 4XX response.

    :id: 4b176997-0be2-4bd8-81fd-8b4ef5045382
    :description: Attempt to create sources missing required data.
    :steps: Attempt to create a source missing:
            a) a name
            b) hosts
            c) credential id's
    :expectedresults: Error is thrown and no new source is created.
    """
    cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4())
    cred.create()
    cleanup.append(cred)
    src = Source(
        source_type=src_type,
        client=api.Client(response_handler=api.echo_handler),
        hosts=['localhost'],
        credential_ids=[cred._id],
    )

    # remove field from payload
    delattr(src, field)
    create_response = src.create()
    assert create_response.status_code == 400


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
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
        src_type,
        cleanup,
        shared_client,
        data):
    """Attempt to create a source with invalid data.

    The requests should be met with a 4XX response.

    :id: e8754fd4-8d03-4899-bfde-0fc587d78ae1
    :description: Attempt to create sources missing required data.
    :steps: Attempt to create a source with invalid:
        a) creds
        b) host
        c) name
    :expectedresults: Error is thrown and no new source is created.
    """
    cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4())
    cred.create()
    cleanup.append(cred)
    data['credential_ids'] = cred._id if not data['credential_ids'] else [-1]
    src = Source(
        source_type=src_type,
        client=api.Client(response_handler=api.echo_handler),
        # unpack parametrized arguments
        **data
    )
    create_response = src.create()
    assert create_response.status_code == 400


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
def test_read_all(src_type, cleanup, shared_client):
    """After created, retrieve all network sources with GET to api.

    :id: e708362c-a289-46f1-ad05-724e3e4383d5
    :description: The API should return list with all sources created
        when a GET request is sent to the {network, vcenter} sources endpoint.
    :steps:
        1) Create collection of sources, saving the information.
        2) Send GET request to {network, vcenter} source endpoint to get list
           of created {network, vcenter} sources
        3) Confirm that all sources are in the list.
    :expectedresults: All sources are present in data returned by API.
    """
    created_srcs = []
    for _ in range(random.randint(2, 10)):
        # gen_valid_srcs will take care of cleanup
        created_srcs.append(gen_valid_source(cleanup, src_type, 'localhost'))
    server_srcs = Source().list().json()['results']
    num_srcs = len(created_srcs)
    for server_source in server_srcs:
        for created_source in created_srcs:
            if server_source['id'] == created_source.fields()['id']:
                assert_matches_server(created_source)
                num_srcs -= 1
    # if we found everything we created, then the list should be empty
    assert num_srcs == 0


@pytest.mark.parametrize('src_type', QCS_SOURCE_TYPES)
def test_delete(src_type, cleanup, shared_client):
    """After creating several {network, vcenter} sources, delete one.

    :id: 24d811b1-655d-4278-ab9f-64ca46a7121b
    :description: Test that we can delete an individual {network, vcenter}
        source by id
    :steps:
        1) Create collection of {network, vcenter} sources, saving the
           information.
        2) Send a DELETE request to destroy individual source
        3) Confirm that all sources are on the server except the deleted one.
        4) Repeat until all sources are deleted.
    :expectedresults: All sources are present on the server except the
        deleted source.
    """
    created_srcs = []
    num_srcs = random.randint(2, 20)
    echo_client = api.Client(response_handler=api.echo_handler)
    for i in range(num_srcs):
        # gen_valid_srcs will take care of cleanup
        created_srcs.append(gen_valid_source(cleanup, src_type, 'localhost'))
    for i in range(num_srcs):
        delete_src = created_srcs.pop()
        delete_src.delete()
        delete_src.client = echo_client
        delete_response = delete_src.read()
        assert delete_response.status_code == 404
        for p in created_srcs:
            assert_matches_server(p)


@pytest.mark.skip
def test_type_mismatch(src_type, cleanup, shared_client):
    """Attempt to create sources with credentials of the wrong type.

    For example, if we create a 'network' typed credential, we can not create a
    'vcenter' typed source using this credential.

    :id: 89bc1bb5-127b-48da-b106-82cd1ef7e00a
    :description: Test that we cannot create a source with the wrong type
        of credential.
    :steps:
        1) Create a credential of one type
        2) Attempt to create a source with that credential of a different type
    :expectedresults: An error is thrown and no new source is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_port_default(src_type, cleanup, shared_client):
    """Test that the correct default port is provided if it is not specified.

    :id: 22af9909-887a-4bea-811c-6ef438a53fdb
    :description: Test that the correct default port is chosen for each type.
    :steps:
        1) Create a credential
        2) Create a source of the same type and do not specify the port
        3) Test that the correct default port is provided based on type.
    :expectedresults: A source is created with sensible default port.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_create_with_port(src_type, cleanup, shared_client):
    """Test that we may create with a custom port specified.

    :id: 9e83e1ed-e229-4822-a9c3-cbb8a7e4282e
    :description: Test that sources can be created with custom ports.
    :steps:
        1) Create a credential
        2) Create a source of the same type and specify a custom port.
    :expectedresults: A source is created with user specified data.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_negative_invalid_port(src_type, cleanup, shared_client):
    """Test that we are prevented from using a nonsense value for the port.

    :id: e64df701-5819-4e80-a5d2-d26cbc6f71a7
    :description: Test that sources cannot be created with bad values for the
        port.
    :steps:
        1) Create a credential
        2) Attempt to create a source of the same type and specify a custom
           port with various nonsense values like 'foo**' or -1 or None
    :expectedresults: The source is not created
    :caseautomation: notautomated
    """
    pass
