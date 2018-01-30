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

from camayoc import config
from camayoc.constants import SATELLITE_SCAN_TIMEOUT
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.qcs_models import (
    Credential,
    Source,
    Scan
)
from camayoc.tests.qcs.api.v1.utils import wait_until_state


def sat_source():
    """Gather Satellite source from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no source is found.
    """
    try:
        src = [s for s in config.get_config()['qcs']['sources']
               if s['type'] == 'satellite']
    except (ConfigFileNotFoundError, KeyError):
        src = []
    return src


def prep_broken_sat_scan(cleanup, scan_type='connect'):
    """Return a scan that can be created but will fail to complete.

    Create and return a source with a non-existent host and dummy credential.
    It is returned ready to be POSTed to the server via the create() instance
    method.
    """
    bad_cred = Credential(
        username='broken',
        password='broken',
        cred_type='satellite'
    )
    bad_cred.create()
    cleanup.append(bad_cred)
    bad_src = Source(
        source_type='satellite',
        hosts=['1.0.0.0'],
        credential_ids=[bad_cred._id],
        options={'satellite_version': '6.2'}
    )
    bad_src.create()
    cleanup.append(bad_src)
    bad_scn = Scan(
        source_ids=[bad_src._id],
        scan_type=scan_type,
    )
    return bad_scn


def prep_sat_scan(source, cleanup, client, scan_type='connect'):
    """Given a source from config file, prep the scan.

    Takes care of creating the Credential and Source objects on the server and
    staging them for cleanup after the tests complete.
    """
    cfg = config.get_config()
    cred_ids = []
    for c in cfg['credentials']:
        if c['name'] in source['credentials'] and c['type'] == 'satellite':
            cred = Credential(
                cred_type='satellite',
                client=client,
                password=c['password'],
                username=c['username'],
            )
            cred.create()
            cleanup.append(cred)
            cred_ids.append(cred._id)
    satsrc = Source(
        source_type='satellite',
        client=client,
        hosts=source['hosts'],
        credential_ids=cred_ids,
        options=source.get('options')
    )
    satsrc.create()
    cleanup.append(satsrc)
    scan = Scan(source_ids=[satsrc._id], scan_type=scan_type)
    return scan


@pytest.mark.parametrize('scan_type', ['connect', 'inspect'])
@pytest.mark.parametrize('source', sat_source())
def test_create(shared_client, cleanup, source, scan_type):
    """Run a scan on a system and confirm it completes.

    :id: 52835270-dba9-4a68-bd36-225e0ef4679b
    :description: Create a satellite scan and assert that it completes
    :steps:
        1) Create satellite credential
        2) Create satellite source
        3) Create a satellite scan
        4) Assert that the scan completes
    :expectedresults: A scan is run and reaches completion
        Also, scan results should be available during the scan.
    """
    scan = prep_sat_scan(source, cleanup, shared_client, scan_type)
    scan.create()
    if scan_type == 'inspect':
        wait_until_state(scan, state='running')
        assert 'connection_results' in scan.results().json().keys()
        assert 'inspection_results' in scan.results().json().keys()
    wait_until_state(scan, state='completed', timeout=SATELLITE_SCAN_TIMEOUT)


@pytest.mark.parametrize('scan_type', ['connect', 'inspect'])
@pytest.mark.parametrize('source', sat_source())
def test_negative_create(shared_client, cleanup, source, scan_type):
    """Create a scan on for a invalid satellite and confirm it fails.

    :id: 7d2349dd-0c1c-41b2-8b20-7aaa2a45d64c
    :description: Create a scan for an invalid satellite and assert that it
        fails
    :steps:
        1) Create satellite credential
        2) Create satellite source for invalid satellite
        3) Create a satellite scan
        4) Assert that the scan fails
    :expectedresults: A scan is run and reaches completion
    """
    scan = prep_broken_sat_scan(cleanup, scan_type)
    scan.create()
    wait_until_state(scan, state='failed', timeout=SATELLITE_SCAN_TIMEOUT)


@pytest.mark.parametrize('scan_type', ['inspect'])
@pytest.mark.parametrize('source', sat_source())
def test_pause_cancel(shared_client, cleanup, source, scan_type):
    """Run a scan on a system and confirm we can pause and cancel it.

    :id: 7d61014a-7791-4f35-8020-6081c7e31227
    :description: Assert that scans can be paused and then canceled.
    :steps:
        1) Create satellite credential
        2) Create satellite source
        3) Create a satellite scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be canceled
    :expectedresults: A satellite scan can be paused and canceled
    """
    scan = prep_sat_scan(source, cleanup, shared_client, scan_type)
    scan.create()
    wait_until_state(scan, state='running', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.cancel()
    wait_until_state(scan, state='canceled', timeout=SATELLITE_SCAN_TIMEOUT)


@pytest.mark.parametrize('scan_type', ['inspect'])
@pytest.mark.parametrize('source', sat_source())
def test_restart(shared_client, cleanup, source, scan_type):
    """Run a scan on a system and confirm we can pause and restart it.

    :id: 6b20ec6e-83c5-4fcc-9f0b-21eacc8f732e
    :description: Assert that scans can be paused and then restarted.
    :steps:
        1) Create satellite credential
        2) Create satellite source
        3) Create a satellite scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be restarted
        6) Assert that he scan completes
    :expectedresults: A restarted scan completes
    """
    scan = prep_sat_scan(source, cleanup, shared_client, scan_type)
    scan.create()
    wait_until_state(scan, state='running', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.restart()
    wait_until_state(scan, state='completed', timeout=SATELLITE_SCAN_TIMEOUT)
