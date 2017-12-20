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


@pytest.mark.skip
def test_negative_create_multiple(shared_client, cleanup, scan_host):
    """Attempt to create a vcenter Source using excess data.

    :id: 5a735a98-a437-4bcd-8abf-9d9644bcc045
    :description: Attempt to create a vcenter source with multiple hosts
    :steps:
        1) Create host credential
        2) Send POST with data to create vcenter source using the host
            credential to the source endpoint with multiple hosts,
            (list, IPv4 range, or ansible pattern like example[1-10].com)
    :expectedresults: An error is thrown and no new host is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_negative_update_invalid(shared_client, cleanup, scan_host):
    """Create a vcenter source and then update it with invalid data.

    :id: d57d8481-54e3-4d9a-b330-80edc9364f37
    :description: Create vcenter source of single host and credential,
        then attempt to update it with multiple {hosts, credentials}
    :steps:
        1) Create a valid vcenter credential and source
        2) Attempt to update with multiple {hosts, credentials}
    :expectedresults: An error is thrown and no new host is created.
    :caseautomation: notautomated
    """
    pass
