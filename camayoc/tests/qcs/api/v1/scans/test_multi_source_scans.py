# coding=utf-8
"""Tests for ``Scan`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""

import pytest

from camayoc.tests.qcs.api.v1.utils import (
    prep_all_source_scan,
    wait_until_state,
)


@pytest.mark.parametrize('scan_type', ['connect', 'inspect'])
def test_multi_source_create(shared_client, cleanup, scan_type):
    """Run a scan on a collection of sources and confirm it completes.

    :id: 43624cc1-6c41-4c2d-9919-c3d0aae83165
    :description: Create sources for each source specified in the
        config file and then create a scan that scans all the sources.
        Provided that the resources are specified in the config file, this
        will test that scans including multiple sources of mixed types can
        be created and complete.
    :steps:
        1) Create all credentials specified in config file
        2) Create all sources specified in config file, using appropriate
           credentials
        3) Create a scan using all sources
        4) Assert that the scan completes and a fact id is generated
    :expectedresults: A scan is run and has facts associated with it
        Also, scan results should be available during the scan.
    """
    scan = prep_all_source_scan(cleanup, shared_client, scan_type)
    scan.create()
    if scan_type == 'inspect':
        wait_until_state(scan, state='running')
        assert 'connection_results' in scan.results().json().keys()
        assert 'inspection_results' in scan.results().json().keys()
    wait_until_state(scan, state='completed', timeout=600)
    if scan_type == 'inspect':
        assert scan.read().json().get('fact_collection_id') > 0
