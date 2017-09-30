# coding=utf-8
"""Tests for ``Host Credential`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: host_credential
:caseimportance: high
:caselevel: integration
:requirement: sonar
:testtype: functional
:upstream: yes
"""
import re

from camayoc import api
from camayoc.qcs_models import HostCredential
from camayoc.constants import MASKED_PASSWORD_OUTPUT


def test_create_with_password(isolated_filesystem, host_cred_cleanup):
    """Create a host credential with username and password.

    :id: d04e3e1b-c7f1-4cc2-a4a4-a3d3317f95ce
    :description: Create a host credential with a user name and password
    :steps: Send POST with necessary data to documented api endpoint.
    :expectedresults: A new host credential entry is created with the data.
    """
    client = api.QCS_Client()
    host = HostCredential()
    host.password = 'foo'
    password_matcher = re.compile(MASKED_PASSWORD_OUTPUT)
    create_response = client.create_host_cred(host.payload())
    host.host_id = create_response.json()['id']
    read_response = client.read_host_creds()
    artifact = None
    for item in read_response.json():
        if host.host_id == item.get('id'):
            artifact = item
    assert artifact is not None
    for key, value in host.fields().items():
        if key == 'password':
            assert password_matcher.match(artifact.get(key))
        else:
            assert artifact.get(key) == value
