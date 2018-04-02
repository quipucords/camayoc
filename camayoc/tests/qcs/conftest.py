"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api
from camayoc.qcs_models import (
    Credential,
    Scan,
    Source,
)


def sort_and_delete(trash):
    """Sort and delete a list of QCSObject typed items in the correct order."""
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
            obj.delete()


@pytest.fixture(scope='function')
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
