# coding=utf-8
"""Tests for ``Host Credential`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: sonar
:testtype: functional
:upstream: yes
"""

from uuid import uuid4

from camayoc import api
from camayoc.qcs_models import HostCredential


def test_create_with_password(isolated_filesystem, test_cleanup):
    """Create a host credential with username and password.

    :id: d04e3e1b-c7f1-4cc2-a4a4-a3d3317f95ce
    :description: Create a host credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new host credential entry is created with the data.
    """
    client = api.QCSClient()
    hostcred = HostCredential(password=str(uuid4()))
    hostcred._id = client.create_host_cred(hostcred.payload()).json()['id']
    created_creds = client.read_host_creds().json()
    assert len(created_creds) == 1
    artifact = created_creds[0]
    assert hostcred == artifact


def test_create_with_sshkey(isolated_filesystem, test_cleanup):
    """Create a host credential with username and sshkey.

    :id: ab6fd574-2e9f-46b8-847d-17b23c19fdd2
    :description: Create a host credential with a user name and sshkey
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new host credential entry is created with the data.
    """
    pass


def test_negative_create_key_and_pass(isolated_filesystem, test_cleanup):
    """Attempt to create a host credential with sshkey and password.

    The request should be met with a 4XX response.

    :id: 22a2ca65-5f9d-4c43-89ad-d7ab53223896
    :description: Create a host credential with username, sshkey, and password.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
    """
    pass


def test_negative_create_no_name(isolated_filesystem, test_cleanup):
    """Attempt to create a host credential missing a name.

    The request should be met with a 4XX response.

    :id: faf2d9fd-8b19-4bf7-b4a9-761da6de34e4
    :description: Create a host credential missing a name.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
    """
    pass


def test_negative_create_no_key_or_pass(
        isolated_filesystem, test_cleanup):
    """Attempt to create a host credential missing both password and sshkey.

    The request should be met with a 4XX response.

    :id: 97a24094-3e9b-4eca-884e-3eda4e461ea1
    :description: Create a host credential missing both password and sshkey.
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: Error is thrown and no new host credential is created.
    """
    pass


def test_read_all(isolated_filesystem, test_cleanup):
    """After created, retrieve all host credentials with GET to api.

    :id: fa05b857-5b01-4388-9226-8dfb5639c815
    :description: The API should return list with all host credentials created
        when a GET request is sent to the host credential endpoint.
    :steps:  1) Create collection of host credentials, saving the information.
        2) Send GET request to host credential endpoint to get list of
            created host credentials.
        3) Confirm that all hosts are in the list.
    :expectedresults: All hosts are present in data returned by API.
    """
    pass


def test_read_indv(isolated_filesystem, test_cleanup):
    """After created, retrieve each host credential with GET to api.

    :id: 4d381119-2dc3-42b6-9b41-e27307d61fcc
    :description: The API should a single host credential when a GET is made
        to the host credentials path and a host id is specified.
    :steps:  1) Create collection of host credentials, saving the information.
        2) Send GET request to host credential endpoint with the host id
            specified.
        3) Confirm that each host is retrieved
    :expectedresults: All hosts are present in data returned by API.
    """
    pass


def test_delete(isolated_filesystem, test_cleanup):
    """After creating several host credentials, delete one.

    :id: e71b521c-59f9-483a-9063-1fbd5087c667
    :description: Test that we can delete an individual host credential by id
    :steps:  1) Create collection of host credentials, saving the information.
        2) Send a DELETE request to destroy individual host credential
        3) Send GET request to host credential endpoint to get list of
            created host credentials.
        4) Confirm that all hosts are in the list except the deleted one.
        5) Repeat until all hosts are deleted.
    :expectedresults: All hosts are present in data returned by API except
        the deleted credential.
    """
    pass
