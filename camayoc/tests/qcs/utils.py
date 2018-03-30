"""Utility functions for quipucords server tests."""
from camayoc import api
from camayoc.qcs_models import Credential, Source
from camayoc.utils import uuid4


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
        if key == 'options' and original_data.get(key) is None:
            continue
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


def gen_valid_source(cleanup, src_type, host, create=True):
    """Create valid source."""
    cred = Credential(cred_type=src_type, password=uuid4())
    cred.create()
    cleanup.append(cred)
    source = Source(
            source_type=src_type,
            hosts=[host],
            credential_ids=[cred._id],
                    )
    if create:
        source.create()
        cleanup.append(source)
        assert_matches_server(source)
    return source
