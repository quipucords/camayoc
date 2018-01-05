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
from camayoc.tests.qcs.api.v1.scans.utils import wait_until_state


def sat_source():
    """Gather Satellite source from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no source is found.
    """
    try:
        src = [config.get_config()['satellite']]
    except (ConfigFileNotFoundError, KeyError):
        src = []
    return src


def prep_broken_sat_scan(cleanup):
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
    )
    bad_src.create()
    cleanup.append(bad_src)
    bad_scn = Scan(
        source_ids=[bad_src._id],
    )
    return bad_scn


def prep_sat_scan(source, cleanup, client):
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
        hosts=[source['hostname']],
        credential_ids=cred_ids,
    )
    satsrc.create()
    cleanup.append(satsrc)
    scan = Scan(source_ids=[satsrc._id])
    return scan


@pytest.mark.skip
@pytest.mark.create
@pytest.mark.parametrize('source', sat_source())
def test_create(shared_client, cleanup, source):
    """Run a scan on a system and confirm it completes.

    :id: 52835270-dba9-4a68-bd36-225e0ef4679b
    :description: Create a satellite scan and assert that it completes
    :steps:
        1) Create satellite credential
        2) Create satellite source
        3) Create a satellite scan
        4) Assert that the scan completes
    :expectedresults: A scan is run and reaches completion
    :caseautomation: notautomated
    """
    scan = prep_sat_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='completed', timeout=SATELLITE_SCAN_TIMEOUT)


@pytest.mark.skip
@pytest.mark.parametrize('source', sat_source())
def test_pause_cancel(shared_client, cleanup, source):
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
    :caseautomation: notautomated
    """
    scan = prep_sat_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.cancel()
    wait_until_state(scan, state='canceled', timeout=SATELLITE_SCAN_TIMEOUT)


@pytest.mark.skip
@pytest.mark.parametrize('source', sat_source())
def test_restart(shared_client, cleanup, source):
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
    :caseautomation: notautomated
    """
    scan = prep_sat_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=SATELLITE_SCAN_TIMEOUT)
    scan.restart()
    wait_until_state(scan, state='running', timeout=SATELLITE_SCAN_TIMEOUT)
    wait_until_state(scan, state='completed', timeout=SATELLITE_SCAN_TIMEOUT)
