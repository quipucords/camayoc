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

from camayoc import api
from camayoc.qcs_models import HostCredential
from camayoc.qcs_models import NetworkProfile

CREATE_DATA = ['localhost', '127.0.0.1']


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_create(isolated_filesystem, test_cleanup, scan_host):
    """Create a Network Profile using a single credential.

    :id: db459fc2-d34c-45cf-915a-1535406a9320
    :description: Create network profile of single host and credential
    :steps: 1) Create host credential
        2) Send POST with data to create network profile using the host
            credential to the profile endpoint.
    :expectedresults: A new network profile entry is created with the data.
    """
    hostcred = HostCredential(password='foo')
    client = api.QCSClient()
    hostcred._id = client.create_host_cred(hostcred.payload()).json()['id']
    netprof = NetworkProfile(
        hosts=[scan_host],
        credential_ids=[
            hostcred._id])
    netprof._id = client.create_net_prof(netprof.payload()).json()['id']
    artifact = client.read_net_profs(net_prof_id=netprof._id).json()
    assert netprof == artifact
