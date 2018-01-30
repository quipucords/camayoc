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
import time


from camayoc.utils import uuid4
from camayoc.qcs_models import (
    Credential,
    Source,
)
from camayoc.tests.qcs.api.v1.utils import (
    wait_until_state,
    prep_broken_scan,
    prep_network_scan,
    network_sources,
    first_network_source,
)


@pytest.mark.parametrize('scan_type', ['connect', 'inspect'])
@pytest.mark.parametrize('source', network_sources(), ids=[
                         '{}-{}'.format(
                             s['name'],
                             s['credentials']) for s in network_sources()]
                         )
def test_create(shared_client, cleanup, source, scan_type):
    """Run a scan on a system and confirm it completes.

    :id: ee3b0bc8-1489-443e-86bb-e2a2349e9c98
    :description: Create a scan and assert that it completes
    :steps:
        1) Create host credential
        2) Send POST with data to create network source using the host
           credential to the source endpoint.
        3) Create a scan
        4) Assert that the scan completes and a fact id is generated
    :expectedresults: A scan is run and has facts associated with it
        Also, scan results should be available during the scan.
    """
    scan = prep_network_scan(source, cleanup, shared_client, scan_type)
    scan.create()
    if scan_type == 'inspect':
        wait_until_state(scan, state='running')
        assert 'connection_results' in scan.results().json().keys()
        assert 'inspection_results' in scan.results().json().keys()
    wait_until_state(scan, state='completed')
    if scan_type == 'inspect':
        assert scan.read().json().get('fact_collection_id') > 0


@pytest.mark.parametrize('scan_type', ['connect', 'inspect'])
@pytest.mark.parametrize('source', network_sources(), ids=[
                         '{}-{}'.format(
                             s['name'],
                             s['credentials']) for s in network_sources()]
                         )
def test_run_mixed_reachable(shared_client, cleanup, source, scan_type):
    """Run a scan that includes reachable and unreachable hosts.

    :id: f5f61ab1-d63e-40de-8546-6b2a6f8afb56
    :description: Create a scan that has two sources, one that is known to
        have all reachable, and the other that is constructed to have no
        reachable hosts. The scan should complete, but show a failed
        status for inspect scans. However, it still should have been
        able to create a fact collection for those facts it was able to
        collect.
    :steps:
        1) Create a scan that includes reachable and unreachable hosts
        2) Assert that the scan completes and a fact id is generated
    :expectedresults: A scan is run and has facts associated with it
        Also, scan results should be available during the scan.
    """
    scan = prep_network_scan(source, cleanup, shared_client, scan_type)
    cred = Credential(cred_type='network', username=uuid4(), password=uuid4())
    cred.create()
    cleanup.append(cred)
    bad_src = Source(
        source_type='network',
        hosts=['example.com'],
        credential_ids=[
            cred._id])
    bad_src.create()
    cleanup.append(bad_src)
    scan.sources.append(bad_src._id)
    scan.create()
    if scan_type == 'inspect':
        wait_until_state(scan, state='running')
        assert 'connection_results' in scan.results().json().keys()
        assert 'inspection_results' in scan.results().json().keys()
    if scan_type == 'connect':
        wait_until_state(scan, state='completed')
    if scan_type == 'inspect':
        wait_until_state(scan, state='failed')
        assert scan.read().json().get('fact_collection_id') > 0


@pytest.mark.parametrize('scan_type', ['inspect'])
def test_negative_create(shared_client, cleanup, scan_type):
    """Run a scan on a system that we cannot access and confirm that it fails.

    :id: 0d132fde-1c3f-4f81-b425-26adf4806c04
    :description: Create a scan for a network source that we lack actual
        credentials for, and assert that it fails
    :steps:
        1) Create a scan that should fail
        2) Assert that the scan fails
    :expectedresults: A scan is run and has facts associated with it
    """
    scan = prep_broken_scan('network', cleanup, scan_type)
    scan.create()
    wait_until_state(scan, state='failed')


@pytest.mark.parametrize('source', first_network_source(), ids=[
                         '{}-{}'.format(
                             first_network_source()[0]['name'],
                             first_network_source()[0]['credentials'])]
                         )
def test_pause_cancel(shared_client, cleanup, source):
    """Run a scan on a system and confirm we can pause and cancel it.

    :id: 4d4b9839-1672-4183-bd27-11864787eb8e
    :description: Assert that scans can be paused and then canceled.
    :steps:
        1) Create host credential
        2) Send POST with data to create network source using the host
           credential to the source endpoint.
        3) Create a scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be canceled
    :expectedresults: A scan can be paused and canceled
    """
    scan = prep_network_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running')
    scan.pause()
    wait_until_state(scan, state='paused')
    scan.cancel()
    wait_until_state(scan, state='canceled')


@pytest.mark.parametrize('source', first_network_source(), ids=[
                         '{}-{}'.format(
                             first_network_source()[0]['name'],
                             first_network_source()[0]['credentials'])]
                         )
def test_restart(shared_client, cleanup, source):
    """Run a scan on a system and confirm we can pause and restart it.

    :id: 6d81121d-500e-4188-8195-2e469ca606c0
    :description: Assert that scans can be paused and then restarted.
    :steps:
        1) Create host credential
        2) Send POST with data to create network source using the host
           credential to the source endpoint.
        3) Create a scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be restarted
        6) Assert that he scan completes
    :expectedresults: A restarted scan completes
    """
    scan = prep_network_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running')
    scan.pause()
    wait_until_state(scan, state='paused')
    scan.restart()
    wait_until_state(scan, state='running')
    wait_until_state(scan, state='completed')
    assert scan.read().json().get('fact_collection_id') > 0


@pytest.mark.parametrize('source', first_network_source(), ids=[
                         '{}-{}'.format(
                             first_network_source()[0]['name'],
                             first_network_source()[0]['credentials'])]
                         )
def test_queue_mix_valid_invalid(shared_client, cleanup, source):
    """Create a series of scans and assert all valid ones complete.

    :id: eb6d07bd-39c5-4f9a-ae34-791c95f315fb
    :description: Ensure scans can progress in queue to completion.
    :steps:
        1) Create a series of scans that include some that should succeed and
           some that should fail, either because the host does not exist or
           the credential used won't give you access to it.
        2) Assert that all valid scans complete
        3) Assert all invalid scans fail
    :expectedresults: A queue will progress even if some scans fail
    """
    good_scans = []
    bad_scans = []
    for k in range(6):
        time.sleep(2)
        if not k % 2:
            bad_scn = prep_broken_scan('network', cleanup)
            bad_scn.create()
            bad_scans.append(bad_scn)
        else:
            scan = prep_network_scan(source, cleanup, shared_client)
            scan.create()
            good_scans.append(scan)

    for scan in good_scans:
        wait_until_state(scan)
    assert scan.read().json().get('fact_collection_id') > 0

    for scan in bad_scans:
        wait_until_state(scan, state='failed', timeout=240)


@pytest.mark.parametrize('source', first_network_source(), ids=[
                         '{}-{}'.format(
                             first_network_source()[0]['name'],
                             first_network_source()[0]['credentials'])]
                         )
def test_queue_mix_paused_canceled(shared_client, cleanup, source):
    """Assert all non-canceled and paused scans in a queue complete.

    :id: 925e2a72-3e69-4947-bfd7-5298bc033963
    :description: Ensure scans can progress in queue that contains paused and
        canceled scans to completion.
    :steps:
        1) Create a series of valid scans
        2) Pause and cancel a random selection of scans
        3) Assert that all non-paused/canceled scans complete
        4) Restart the paused scans and assert they complete
        5) Assert the canceled scans stay canceled
    :expectedresults: All non-paused/canceled scans will progress in queue
    """
    good_scans = []
    paused_scans = []
    canceled_scans = []
    for k in range(7):
        if k in [0, 3]:
            scan = prep_network_scan(source, cleanup, shared_client)
            scan.create()
            wait_until_state(scan, state='running')
            scan.pause()
            wait_until_state(scan, state='paused')
            paused_scans.append(scan)
        if k in [2, 5]:
            scan = prep_network_scan(source, cleanup, shared_client)
            scan.create()
            wait_until_state(scan, state='running')
            scan.cancel()
            wait_until_state(scan, state='canceled')
            canceled_scans.append(scan)
        else:
            scan = prep_network_scan(source, cleanup, shared_client)
            scan.create()
            good_scans.append(scan)

    for scan in good_scans:
        wait_until_state(scan, state='completed')
        assert scan.read().json().get('fact_collection_id') > 0
