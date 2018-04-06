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

import pytest

from camayoc import api
from camayoc.constants import QPC_HOST_MANAGER_TYPES
from camayoc.qpc_models import (
    Credential,
    Source,
)
from camayoc.tests.qpc.utils import (assert_source_create_fails,
                                     assert_source_update_fails)
from camayoc.utils import uuid4

INVALID_HOST_DATA = [['192.0.2.[0:255]'], ['192.0.3.0/24']]
VALID_HOST_DATA = [['192.0.2.1'], ['192.0.2.10']]


@pytest.mark.parametrize('scan_host', INVALID_HOST_DATA)
@pytest.mark.parametrize('src_type', QPC_HOST_MANAGER_TYPES)
def test_negative_create_multiple(src_type, shared_client, cleanup, scan_host):
    """Attempt to create a host manager Source using excess data.

    :id: 5a735a98-a437-4bcd-8abf-9d9644bcc045
    :description: Any attempt to create a host manager source with multiple
        hosts, multiple credentials, or both should be rejected.
    :steps:
        1) Create necessary credentials.
        2) Send POST with data to create a host manager source using either
            multiple credentials or multiple hosts (could be list, IPv4 range,
            or ansible pattern like example[1-10].com)
    :expectedresults: An error is thrown and no new host is created.
    """
    # initialize & create multiple credentials
    cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4()
    )
    cred2 = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4()
    )
    cred.create()
    cred2.create()

    # initialize source object using multiple hosts
    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=scan_host,
        credential_ids=[cred._id],
    )
    assert_source_create_fails(src)

    # initialize source object using multiple creds
    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=VALID_HOST_DATA[0],
        credential_ids=[cred._id, cred2._id],
    )
    assert_source_create_fails(src)

    # initialize source object using multiple creds & hosts
    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=scan_host,
        credential_ids=[cred._id, cred2._id],
    )
    assert_source_create_fails(src)

    cleanup.extend([cred, cred2])


@pytest.mark.parametrize('invalid_host', INVALID_HOST_DATA)
@pytest.mark.parametrize('scan_host', VALID_HOST_DATA)
@pytest.mark.parametrize('src_type', QPC_HOST_MANAGER_TYPES)
def test_negative_update_invalid(src_type, shared_client, cleanup, scan_host,
                                 invalid_host):
    """Create a host manager source and then update it with invalid data.

    :id: d57d8481-54e3-4d9a-b330-80edc9364f37
    :description: Create host manager source of single host and credential,
        then attempt to update it with multiple {hosts, credentials}
    :steps:
        1) Create a valid host manager credential and source
        2) Attempt to update with multiple {hosts, credentials}
    :expectedresults: An error is thrown and no new host is created.
    """
    # initialize & create original credential & source
    pwd_cred = Credential(
        cred_type=src_type,
        client=shared_client,
        password=uuid4()
    )
    pwd_cred.create()

    src = Source(
        source_type=src_type,
        client=shared_client,
        hosts=scan_host,
        credential_ids=[pwd_cred._id],
    )
    src.create()

    # Create extra credential for update
    cred2 = Credential(
        cred_type='network',
        client=shared_client,
        password=uuid4()
    )
    cred2 .create()

    # add the ids to the lists to destroy after the test is done
    cleanup.extend([pwd_cred, src, cred2])
    original_data = copy.deepcopy(src.fields())
    src.client = api.Client(api.echo_handler)

    # Try to update with multiple credentials
    src.credentials = [pwd_cred._id, cred2._id]
    assert_source_update_fails(original_data, src)

    # Try to update with multiple hosts
    src.hosts = invalid_host
    assert_source_update_fails(original_data, src)

    # Try to update with multiple hosts & creds
    src.hosts = invalid_host
    src.credentials = [pwd_cred._id, cred2._id]
