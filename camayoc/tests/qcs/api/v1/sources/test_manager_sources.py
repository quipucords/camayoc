# coding=utf-8
"""Tests for ``Source`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import pytest

from camayoc.constants import QCS_HOST_MANAGER_TYPES


@pytest.mark.skip
@pytest.mark.parametrize('src_type', QCS_HOST_MANAGER_TYPES)
def test_negative_create_multiple(src_type, shared_client, cleanup, scan_host):
    """Attempt to create a host manager Source using excess data.

    :id: 5a735a98-a437-4bcd-8abf-9d9644bcc045
    :description: Any attempt to create a host manager source with multiple
        hosts, multiple credentials, or both should be rejected.
    :steps:
        1) Create necessary credentials.
        2) Send POST with data to create a host manager source using either
            multiple credentials or multiple hosts (could be list, IPv4 range,
            or ansible pattern like example[1-10].com)
    :expectedresults: An error is thrown and no new host is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
@pytest.mark.parametrize('src_type', QCS_HOST_MANAGER_TYPES)
def test_negative_update_invalid(src_type, shared_client, cleanup, scan_host):
    """Create a host manager source and then update it with invalid data.

    :id: d57d8481-54e3-4d9a-b330-80edc9364f37
    :description: Create host manager source of single host and credential,
        then attempt to update it with multiple {hosts, credentials}
    :steps:
        1) Create a valid host manager credential and source
        2) Attempt to update with multiple {hosts, credentials}
    :expectedresults: An error is thrown and no new host is created.
    :caseautomation: notautomated
    """
    pass
