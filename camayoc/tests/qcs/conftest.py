"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api


@pytest.fixture
def host_cred_cleanup(request):
    """Fixture that cleans up any created host credentials."""
    def cleanup():
        client = api.QCS_Client()
        read_response = client.read_host_creds()
        for host in read_response.json():
            if host.get('id'):
                client.delete_host_cred(host.get('id'))
    request.addfinalizer(cleanup)
