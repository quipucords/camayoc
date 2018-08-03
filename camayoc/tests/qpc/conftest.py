"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api
from camayoc.qpc_models import Credential, Scan, Source


@pytest.fixture(scope='function')
def sort_and_delete(trash):
    """Sort and delete a list of QPCObject typed items in the correct order."""
    creds = []
    sources = []
    scans = []
    # first sort into types because we have to delete scans before sources
    # and sources before scans
    for obj in trash:
        if isinstance(obj, Credential):
            creds.append(obj)
            continue
        if isinstance(obj, Source):
            sources.append(obj)
            continue
        if isinstance(obj, Scan):
            scans.append(obj)
            continue

    for collection in [scans, sources, creds]:
        for obj in collection:
            # It may have been a while since this object was created, so we
            # will log its client back in to the server and get a fresh token
            obj.client.login()
            # Only assert that we do not hit an internal server error, in case
            # for some reason the object was allready cleaned up by the test
            obj.client.response_handler = api.echo_handler
            response = obj.delete()
            assert response.status_code < 500


def cleanup():
    """Fixture that cleans up any created quipucords objects after a test."""
    trash = []

    yield trash

    sort_and_delete(trash)


@pytest.fixture(scope='session')
def session_cleanup():
    """Fixture that cleans up created quipucords objects after a session."""
    trash = []

    yield trash

    sort_and_delete(trash)


@pytest.fixture()
def shared_client():
    """Yeild a single instance of api.Client() to a test.

    yeilds an api.Client() instance with the standard return code handler.

    .. warning::
       If you intend to change the return code handler, it would be best not to
       use the shared client to avoid possible problems when running tests in
       parallel.
    """
    client = api.Client()
    yield client
