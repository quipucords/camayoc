"""Utility functions for quipucords server tests."""

from camayoc import api
from camayoc.utils import uuid4
from camayoc.qcs_models import HostCredential, NetworkProfile


def assert_matches_server(qcsobject):
    """Assert that the data on the server matches this object."""
    other = qcsobject.read().json()
    assert qcsobject.equivalent(other)


def assert_profile_update_fails(original_data, profile):
    """Assert that the update method on this profile fails.

    :param original_data: This should be the json you expect to match the
        server. This can be collected from your object via profile.fields()
        before altering the object with the invalid data.
    """
    # replace whatever client the profile had with one that won't raise
    # exceptions
    orig_client = profile.client
    profile.client = api.Client(response_handler=api.echo_handler)
    update_response = profile.update()
    assert update_response.status_code == 400
    server_data = profile.read().json()
    for key, value in server_data.items():
        if key == 'credentials':
            # the server creds are dicts with other data besides the id
            cred_ids = []
            for cred in value:
                cred_ids.append(cred.get('id'))
            assert sorted(original_data.get(key)) == sorted(cred_ids)
        else:
            assert original_data.get(key) == value
    # give the profile its original client back
    profile.client = orig_client


def gen_valid_profile(cleanup, host):
    """Create valid profile and return it with echo_handler."""
    client = api.Client()
    cred = HostCredential(client=client, password=uuid4())
    cred.create()
    cleanup.append(cred)
    profile = NetworkProfile(
        hosts=[host],
        credential_ids=[cred._id],
        client=client,
    )
    profile.create()
    cleanup.append(profile)
    assert_matches_server(profile)
    profile.client.response_handler = api.echo_handler
    return profile
