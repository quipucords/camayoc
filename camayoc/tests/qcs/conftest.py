"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api


@pytest.fixture
def cleanup_credentials():
    """Fixture that cleans up any created host credentials."""
    credential_ids = []

    yield credential_ids

    client = api.QCSClient()
    for _id in credential_ids:
        client.delete_credential(_id)


@pytest.fixture
def cleanup_profiles():
    """Fixture that cleans up any created network profiles."""
    profile_ids = []

    yield profile_ids

    client = api.QCSClient()
    for _id in profile_ids:
        client.delete_profile(_id)
