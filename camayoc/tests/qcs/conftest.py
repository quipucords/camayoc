"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api


@pytest.fixture
def cleanup():
    """Fixture that cleans up any created host credentials."""
    trash = []

    yield trash

    for obj in trash:
        obj.delete()


@pytest.fixture(scope='module')
def shared_client():
    """Yeild a single instance of api.Client() to many tests as fixture.

    yeilds an api.Client() instance with the standard return code handler.

    .. warning::
       If you intend to change the return code handler, it would be best not to
       use the shared client to avoid possible problems when running tests in
       parallel.
    """
    client = api.Client()
    yield client
