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

from camayoc import api
from camayoc.qcs_models import HostCredential
from camayoc.qcs_models import NetworkProfile

CREATE_DATA = ['localhost', '127.0.0.1']


@pytest.mark.parametrize('scan_host', CREATE_DATA)
def test_create(
        credentials_to_cleanup,
        profiles_to_cleanup,
        scan_host):
    """Create a Network Profile using a single credential.

    :id: db459fc2-d34c-45cf-915a-1535406a9320
    :description: Create network profile of single host and credential
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
    :expectedresults: A new network profile entry is created with the data.
    """
    cred = HostCredential(password=str(uuid4()))
    client = api.QCSClient()
    cred._id = client.create_credential(cred.payload()).json()['id']
    profile = NetworkProfile(
        hosts=[scan_host],
        credential_ids=[cred._id],
    )
    profile._id = client.create_profile(profile.payload()).json()['id']

    # add the ids to the lists to destroy after the test is done
    credentials_to_cleanup.append(cred._id)
    profiles_to_cleanup.append(profile._id)

    artifact = client.read_profiles(profile_id=profile._id).json()
    assert profile == artifact
