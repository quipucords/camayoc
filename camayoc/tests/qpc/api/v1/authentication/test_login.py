# coding=utf-8
"""Test that we can log in and out of the server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
:upstream: yes
"""
import pytest
import requests

from camayoc import api
from camayoc import config
from camayoc.constants import QPC_CREDENTIALS_PATH
from camayoc.constants import QPC_SCAN_PATH
from camayoc.constants import QPC_SOURCE_PATH


def test_login():
    """Test that we can login to the server.

    :id: 2eb55229-4e1e-4d35-ac4a-4f2424d37cf6
    :description: Test that we can login to the server
    :steps: Send POST with username and password to the token endpoint
    :expectedresults: Receive an authorization token that we can then use
        to build our authentication headers and make authenticated requests.
    """
    client = api.Client(authenticate=False)
    response = client.login()
    data = response.json()
    assert data.get("token"), "No authentication 'token' received"
    client.get(QPC_SOURCE_PATH)


def test_logout():
    """Test that we can log out to the server.

    :id: c4244b27-bfda-454a-a22f-6fb05b900e09
    :description: Test that we can logout to the server
    :steps:
        1) Log into the server
        2) Log out of the server
    :expectedresults: Logged out with success.
    """
    client = api.Client(authenticate=False)
    client.login()
    client.logout()


@pytest.mark.parametrize("endpoint", [QPC_SOURCE_PATH, QPC_CREDENTIALS_PATH, QPC_SCAN_PATH])
def test_forbidden(endpoint):
    """Test that we can't access the server without a token.

    :id: ca51b2a0-1e33-491d-8bb2-5e81d135424d
    :description: Test if we are logged out of the server, then we are forbidden to reach endpoints
    :steps:
        1) Log into the server
        2) Log out of the server
        3) Try an access the server
    :expectedresults: Our request missing a valid auth token is rejected.
    """
    client = api.Client(authenticate=False)
    client.login()
    client.logout()
    with pytest.raises(requests.HTTPError):
        # now that we are logged out, we should get rejected
        client.get(endpoint)


def test_user():
    """Test that when we log in the server reports our username.

    :id: addd7d83-961a-4cdf-9473-7c6db93e6af9
    :description: Test that we can see who is logged into the server
    :steps:
        1) Log into the server
        2) Sent GET request to find out what user is logged in
        3) Assert that it is the user we logged in as
    :expectedresults: The server correctly reports our username.
    """
    client = api.Client()
    qpc_user = config.get_config().get("qpc", {}).get("username")
    assert client.get_user().json()["username"] == qpc_user
