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
from pathlib import Path

import pytest

from camayoc import api
from camayoc.utils import uuid4
from camayoc.qcs_models import (
    Credential,
    Source,
)

from camayoc.tests.qcs.utils import (
    assert_matches_server,
    assert_source_update_fails,
)

NETWORK_TYPE = 'network'
CREATE_DATA = ['localhost', '127.0.0.1', 'example.com']
HOST_FORMAT_DATA = [['192.0.2.[0:255]', '192.0.3.0/24']]
RESULTING_HOST_FORMAT_DATA = ['192.0.2.[0:255]', '192.0.3.[0:255]']
MIXED_DATA = CREATE_DATA + HOST_FORMAT_DATA


@pytest.mark.parametrize('scan_host', HOST_FORMAT_DATA)
def test_create_multiple_hosts(shared_client, cleanup, scan_host):
    """Create a Network Source using multiple hosts.

    :id: 248f701c-b4d4-408a-80b0-c4863a8007e1
    :description: Create a network source with multiple hosts
    :steps:
        1) Create credential
        2) Send POST with data to create network source using the
           credential to the source endpoint with multiple hosts,
           (list, IPv4 range, CIDR notation, or other ansible pattern)
    :expectedresults: The source is created.
    """
    cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        password=uuid4()
    )
    cred.create()
    src = Source(
        source_type=NETWORK_TYPE,
        client=shared_client,
        hosts=scan_host,
        credential_ids=[cred._id],
    )
    src.create()

    # add the ids to the lists to destroy after the test is done
    cleanup.extend([cred, src])

    src.hosts = RESULTING_HOST_FORMAT_DATA
    assert_matches_server(src)


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_create_multiple_creds(
        shared_client,
        cleanup,
        scan_host,
        isolated_filesystem):
    """Create a Network Source using multiple credentials.

    :id: dcf6ea99-c6b1-493d-9db8-3ec0ea09b5e0
    :description: Create a network source with multiple credentials
    :steps:
        1) Create multiple credentials using both sshkey and passwords
        2) Send POST with data to create network source using the credentials
    :expectedresults: The source is created.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    ssh_key_cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    ssh_key_cred.create()
    pwd_cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        password=uuid4()
    )
    pwd_cred.create()

    src = Source(
        source_type=NETWORK_TYPE,
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[ssh_key_cred._id, pwd_cred._id],
    )
    src.create()
    # add the ids to the lists to destroy after the test is done
    cleanup.extend([ssh_key_cred, pwd_cred, src])

    assert_matches_server(src)


@pytest.mark.parametrize('scan_host', MIXED_DATA)
def test_create_multiple_creds_and_sources(
        shared_client,
        cleanup,
        scan_host,
        isolated_filesystem):
    """Create a Network Source using multiple credentials.

    :id: 07f49731-0162-4eb1-b89a-3c95fddad428
    :description: Create a network source with multiple credentials
    :steps:
        1) Create multiple credentials using both sshkey and passwords
        2) Send POST with data to create network source using the credentials
           using a list of sources using multiple formats (alphabetical name,
           CIDR, individual IPv4 address, etc.)
    :expectedresults: The source is created.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    ssh_key_cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    ssh_key_cred.create()
    pwd_cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        password=uuid4()
    )
    pwd_cred.create()

    input_hosts = [scan_host]
    if isinstance(scan_host, list):
        input_hosts = scan_host
    src = Source(
        source_type=NETWORK_TYPE,
        client=shared_client,
        hosts=input_hosts,
        credential_ids=[ssh_key_cred._id, pwd_cred._id],
    )
    src.create()

    # add the ids to the lists to destroy after the test is done
    cleanup.extend([ssh_key_cred, pwd_cred, src])

    if isinstance(scan_host, list):
        src.hosts = RESULTING_HOST_FORMAT_DATA
    assert_matches_server(src)


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_negative_update_invalid(
        shared_client,
        cleanup,
        isolated_filesystem,
        scan_host):
    """Create a network source and then update it with invalid data.

    :id: e0d72f2b-2490-445e-b646-f06ceb4ad23f
    :description: Create network source of single host and credential,
        then attempt to update it with multiple invalid {hosts, credentials}
    :steps:
        1) Create a valid network credential and source
        2) Attempt to update with multiple invalid {hosts, credentials}
    :expectedresults: An error is thrown and no new host is created.
    """
    ssh_keyfile = Path(uuid4())
    ssh_keyfile.touch()

    net_cred = Credential(
        cred_type=NETWORK_TYPE,
        client=shared_client,
        ssh_keyfile=str(ssh_keyfile.resolve()),
    )
    net_cred.create()
    sat_cred = Credential(
        cred_type='satellite',
        client=shared_client,
        password=uuid4()
    )
    sat_cred.create()

    src = Source(
        source_type=NETWORK_TYPE,
        client=shared_client,
        hosts=[scan_host],
        credential_ids=[net_cred._id],
    )
    src.create()

    # add the ids to the lists to destroy after the test is done
    cleanup.extend([net_cred, sat_cred, src])

    original_data = copy.deepcopy(src.fields())
    src.client = api.Client(api.echo_handler)

    # Try to update with invalid credential type
    src.credentials = [sat_cred._id]
    assert_source_update_fails(original_data, src)
    src.hosts = ['1**2@33^']
    assert_source_update_fails(original_data, src)
