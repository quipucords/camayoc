"""Utility functions for quipucords server tests."""


def assert_matches_server(qcsobject):
    """Assert that the data on the server matches this object."""
    other = qcsobject.read().json()
    assert qcsobject.equivalent(other)
