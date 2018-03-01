"""Pytest customizations and fixtures for the quipucords tests."""
import pytest

from camayoc import api
from camayoc.qcs_models import (
    Credential,
    Scan,
    Source,
)


@pytest.fixture
def cleanup():
    """Fixture that cleans up any created host credentials."""
    trash = []

    yield trash

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
