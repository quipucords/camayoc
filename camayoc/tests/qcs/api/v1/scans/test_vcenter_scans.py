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
from camayoc.constants import VCENTER_SCAN_TIMEOUT
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.qcs_models import (
    Credential,
    Source,
    Scan
)
from camayoc.tests.qcs.api.v1.scans.utils import wait_until_state


def vcenter_source():
    """Gather vcenter sources from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no sources are found.
    """
    try:
        src = [s for s in config.get_config()['qcs']['sources']
               if s['type'] == 'vcenter']
    except (ConfigFileNotFoundError, KeyError):
        src = []
    return src


def prep_vcenter_scan(source, cleanup, client):
    """Given a source from config file, prep the scan.

    Takes care of creating the Credential and Source objects on the server and
    staging them for cleanup after the tests complete.
    """
    cfg = config.get_config()
    cred_ids = []
    for c in cfg['credentials']:
        if c['name'] in source['credentials'] and c['type'] == 'vcenter':
            cred = Credential(
                cred_type='vcenter',
                client=client,
                password=c['password'],
                username=c['username'],
            )
            cred.create()
            cleanup.append(cred)
            cred_ids.append(cred._id)

    vcentersrc = Source(
        source_type='vcenter',
        client=client,
        hosts=source['hosts'],
        credential_ids=cred_ids,
    )
    vcentersrc.create()
    cleanup.append(vcentersrc)
    scan = Scan(source_ids=[vcentersrc._id])
    return scan


@pytest.mark.create
@pytest.mark.parametrize('source', vcenter_source())
def test_create(shared_client, cleanup, source):
    """Run a scan on a system and confirm it completes.

    :id: e7d644c1-0a32-4eb4-a663-77b7607491db
    :description: Create a vcenter scan and assert that it completes
    :steps:
        1) Create vcenter credential
        2) Create vcenter source
        3) Create a vcenter scan
        4) Assert that the scan completes
    :expectedresults: A scan is run and reaches completion
    """
    scan = prep_vcenter_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='completed', timeout=VCENTER_SCAN_TIMEOUT)


@pytest.mark.parametrize('source', vcenter_source())
def test_pause_cancel(shared_client, cleanup, source):
    """Run a scan on a system and confirm we can pause and cancel it.

    :id: 1e40a87f-0a99-49de-9d02-f3ced8005a89
    :description: Assert that scans can be paused and then canceled.
    :steps:
        1) Create vcenter credential
        2) Create vcenter source
        3) Create a vcenter scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be canceled
    :expectedresults: A vcenter scan can be paused and canceled
    """
    scan = prep_vcenter_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running', timeout=VCENTER_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=VCENTER_SCAN_TIMEOUT)
    scan.cancel()
    wait_until_state(scan, state='canceled', timeout=VCENTER_SCAN_TIMEOUT)


@pytest.mark.parametrize('source', vcenter_source())
def test_restart(shared_client, cleanup, source):
    """Run a scan on a system and confirm we can pause and restart it.

    :id: bc27c62a-683f-491b-9b99-1e4525594379
    :description: Assert that scans can be paused and then restarted.
    :steps:
        1) Create vcenter credential
        2) Create vcenter source
        3) Create a vcenter scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be restarted
        6) Assert that he scan completes
    :expectedresults: A restarted scan completes
    """
    scan = prep_vcenter_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan, state='running', timeout=VCENTER_SCAN_TIMEOUT)
    scan.pause()
    wait_until_state(scan, state='paused', timeout=VCENTER_SCAN_TIMEOUT)
    scan.restart()
    wait_until_state(scan, state='running', timeout=VCENTER_SCAN_TIMEOUT)
    wait_until_state(scan, state='completed', timeout=VCENTER_SCAN_TIMEOUT)
