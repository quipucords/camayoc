"""Utility functions for quipucords server tests."""
import pytest

from camayoc import api
from camayoc.qpc_models import Credential, Scan, Source
from camayoc.utils import run_scans, uuid4

mark_runs_scans = pytest.mark.skipif(run_scans() is False, reason="RUN_SCANS set to False")
"""Decorator that skips tests if RUN_SCANS environment variable is 'False'."""


def assert_matches_server(qpcobject):
    """Assert that the data on the server matches this object."""
    other = qpcobject.read().json()
    assert qpcobject.equivalent(other)


def assert_source_update_fails(original_data, source):
    """Assert that the update method on this source fails.

    :param original_data: This should be the json you expect to match the
        server. This can be collected from your object via source.fields()
        before altering the object with the invalid data.
    """
    # replace whatever client the source had with one that won't raise
    # exceptions
    orig_client = source.client
    source.client = api.Client(response_handler=api.echo_handler)
    update_response = source.update()
    assert update_response.status_code == 400
    server_data = source.read().json()
    for key, value in server_data.items():
        if key == "options" and original_data.get(key) is None:
            continue
        if key == "credentials":
            # the server creds are dicts with other data besides the id
            cred_ids = []
            for cred in value:
                cred_ids.append(cred.get("id"))
            assert sorted(original_data.get(key)) == sorted(cred_ids)
        else:
            assert original_data.get(key) == value
    # give the source its original client back
    source.client = orig_client


def assert_source_create_fails(source, source_type=""):
    """Assert that the create method of this source fails.

    :param source: The source object.
    """
    # replace whatever client the source had with one that won't raise
    # exceptions
    orig_client = source.client
    source.client = api.Client(response_handler=api.echo_handler)
    create_response = source.create()
    assert create_response.status_code == 400
    expected_errors = [
        {"hosts": ["Source of type vcenter must have a single hosts."]},
        {"credentials": ["Source of type vcenter must have a single credential."]},
        {"hosts": ["Source of type satellite must have a single hosts."]},
        {"credentials": ["Source of type satellite must have a single credential."]},
        {
            "exclude_hosts": [
                "The exclude_hosts option is not valid for source of type " + source_type + "."
            ]
        },
    ]
    response = create_response.json()
    assert response in expected_errors
    # give the source its original client back
    source.client = orig_client


def gen_valid_source(cleanup, src_type, hosts, create=True, exclude_hosts=None):
    """Create valid source."""
    cred = Credential(cred_type=src_type, password=uuid4())
    cred.create()
    cleanup.append(cred)
    source = Source(source_type=src_type, hosts=[hosts], credential_ids=[cred._id])
    # QPC does not accept blank exclude_host values, only add it if not empty.
    if exclude_hosts is not None:
        source.exclude_hosts = [exclude_hosts]
    if create:
        source.create()
        cleanup.append(source)
        assert_matches_server(source)
    return source


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

    client = api.Client(response_handler=api.echo_handler)
    for collection in [scans, sources, creds]:
        for obj in collection:
            # Override client to use a fresh one. It may have been a while
            # since the object was created and its token may be invalid.
            obj.client = client
            # Only assert that we do not hit an internal server error, in case
            # for some reason the object was allready cleaned up by the test
            response = obj.delete()
            assert response.status_code < 500, response.content
