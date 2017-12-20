"""Utility functions for quipucords server tests."""

from camayoc import api
from camayoc.utils import uuid4
from camayoc.qcs_models import Credential, Source


def assert_matches_server(qcsobject):
    """Assert that the data on the server matches this object."""
    other = qcsobject.read().json()
    assert qcsobject.equivalent(other)


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
        if key == 'credentials':
            # the server creds are dicts with other data besides the id
            cred_ids = []
            for cred in value:
                cred_ids.append(cred.get('id'))
            assert sorted(original_data.get(key)) == sorted(cred_ids)
        else:
            assert original_data.get(key) == value
    # give the source its original client back
    source.client = orig_client


def gen_valid_source(cleanup, src_type, host):
    """Create valid source and return it with echo_handler."""
    client = api.Client()
    cred = Credential(cred_type=src_type, client=client, password=uuid4())
    cred.create()
    cleanup.append(cred)
    source = Source(source_type=src_type,
                    hosts=[host],
                    credential_ids=[cred._id],
                    client=client,
                    )
    source.create()
    cleanup.append(source)
    assert_matches_server(source)
    source.client.response_handler = api.echo_handler
    return source
