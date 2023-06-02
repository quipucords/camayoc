"""Utility functions for quipucords server tests."""
import hashlib
from pathlib import Path

import pytest

from camayoc import api
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import Source
from camayoc.utils import uuid4

mark_runs_scans = pytest.mark.skipif(False, reason="We are always running scans now")


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
        {"hosts": ["This source must have a single host."]},
        {"credentials": ["This source must have a single credential."]},
        {"exclude_hosts": ["The exclude_hosts option is not valid for this source."]},
    ]
    response = create_response.json()
    assert response in expected_errors
    # give the source its original client back
    source.client = orig_client


def calculate_sha256sums(directory):
    """Calculate SHA256 sum of all files in directory."""
    directory = Path(directory)
    shasums = {}
    for file in directory.rglob("*"):
        if not file.is_file():
            continue
        key = str(file.relative_to(directory))
        shasum = hashlib.sha256()
        with open(file, "rb") as fh:
            while block := fh.read(4096):
                shasum.update(block)
        shasums[key] = shasum.hexdigest()
    return shasums


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


def get_expected_sha256sums(directory):
    """Find SHA256SUM files in directory and parse them.

    SHA256SUM file names are transformed to be relative to directory arg,
    so output of this function should be strict subset of output of
    `calculate_sha256sums` ran on the same directory.
    """
    directory = Path(directory)
    parsed_shasums = {}
    for file in directory.rglob("*"):
        if file.name != "SHA256SUM":
            continue

        with open(file) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                expected_sum, filename = line.split(maxsplit=1)
                if not filename:
                    continue
                key = str(file.relative_to(directory).with_name(filename))
                parsed_shasums[key] = expected_sum

    return parsed_shasums


def get_object_id(obj):
    """Get id of object whose name is known."""
    if obj._id:
        return obj._id

    available_objs = obj.list(params={"search_by_name": obj.name}).json()
    for received_obj in available_objs.get("results", []):
        if received_obj.get("name") == obj.name:
            return received_obj.get("id")


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
            # Get object id based on the name.
            # This allows us to clean up objects created from UI and CLI.
            # If object id could not be found, assume object was already deleted.
            if not obj._id and obj.name:
                obj._id = get_object_id(obj)
            if obj._id is None:
                continue
            # Only assert that we do not hit an internal server error, in case
            # for some reason the object was already cleaned up by the test
            response = obj.delete()
            assert response.status_code < 500, response.content
