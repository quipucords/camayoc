"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api


@pytest.fixture
def test_cleanup(request):
    """Fixture that cleans up any created host credentials."""
    def cleanup():
        client = api.QCSClient()
        read_response = client.read_host_creds()
        for cred in read_response.json():
            if cred.get('id'):
                client.delete_host_cred(cred.get('id'))
        read_response = client.read_net_profs()
        for prof in read_response.json():
            if prof.get('id'):
                client.delete_net_prof(prof.get('id'))
    request.addfinalizer(cleanup)
