# coding=utf-8
"""Test that we can log in and out of the server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import pytest
import requests

from camayoc import api
from camayoc.constants import (
    QCS_SOURCE_PATH,
    QCS_CREDENTIALS_PATH,
    QCS_SCAN_PATH,
)


def test_login():
    """Test that we can login to the server.

    :id: 2eb55229-4e1e-4d35-ac4a-4f2424d37cf6
    :description: Test that we can login to the server
    :steps: Send POST with username and password to the token endpoint
    :expectedresults: Receive an authorization token that we can then use
        to build our authentication headers and make authenticated requests.
    """
    client = api.Client(authenticate=False)
    client.login()
    client.get(QCS_SOURCE_PATH)


@pytest.mark.parametrize(
    'endpoint', [
        QCS_SOURCE_PATH, QCS_CREDENTIALS_PATH, QCS_SCAN_PATH])
def test_logout(endpoint):
    """Test that we can't access the server without a token.

    :id: ca51b2a0-1e33-491d-8bb2-5e81d135424d
    :description: Test that  to the server
    :steps:
        1) Log into the server
        2) "Logout" of the server (delete our token)
        3) Try an access the server without our token
    :expectedresults: Our request missing an auth token is rejected.
    """
    client = api.Client(authenticate=False)
    client.login()
    client.logout()
    with pytest.raises(requests.HTTPError):
        # now that we are logged out, we should get rejected
        client.get(endpoint)
