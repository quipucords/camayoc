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
def test_create_multiple_hosts(shared_client, cleanup, scan_host):
    """Create a Network Source using multiple hosts.

    :id: 248f701c-b4d4-408a-80b0-c4863a8007e1
    :description: Create a network source with multiple hosts
    :steps:
        1) Create host credential
        2) Send POST with data to create network source using the host
           credential to the source endpoint with multiple hosts,
           (list, IPv4 range, CIDR notation, or other ansible pattern)
    :expectedresults: The source is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_create_multiple_creds(shared_client, cleanup, scan_host):
    """Create a Network Source using multiple credentials.

    :id: dcf6ea99-c6b1-493d-9db8-3ec0ea09b5e0
    :description: Create a network source with multiple credentials
    :steps:
        1) Create multiple host credentials using both sshkey and passwords
        2) Send POST with data to create network source using the credentials
    :expectedresults: The source is created.
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_negative_update_invalid(shared_client, cleanup, scan_host):
    """Create a network source and then update it with invalid data.

    :id: e0d72f2b-2490-445e-b646-f06ceb4ad23f
    :description: Create network source of single host and credential,
        then attempt to update it with multiple invalid {hosts, credentials}
    :steps:
        1) Create a valid network credential and source
        2) Attempt to update with multiple invalid {hosts, credentials}
    :expectedresults: An error is thrown and no new host is created.
    :caseautomation: notautomated
    """
    pass
