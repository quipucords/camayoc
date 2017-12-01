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

from camayoc import config
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.qcs_models import (
    HostCredential,
    NetworkProfile,
    Scan,
)


def profiles():
    """Gather profiles from config file."""
    try:
        profs = config.get_config()['qcs']['profiles']
    except ConfigFileNotFoundError:
        profs = []
    return profs


def wait_until_complete(scan, timeout=120):
    """Wait until the scan has either failed or completed.

    This method should not be called on scan jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 120 seconds, but can be overridden if it is
    anticipated that a scan may take longer to complete.
    """
    if scan.status() in ['paused', 'cancelled']:
        raise UserWarning(
            'You have called wait_until_complete() on a scan '
            'that is paused or cancelled, and this could hang forever.'
            ' This exception has been raised instead.'
            )
    while (
        not scan.status() or not scan.status() in [
            'failed',
            'completed']) and timeout > 0:
        time.sleep(5)
        timeout -= 5


@pytest.mark.parametrize('profile', profiles(), ids=[
                         '{}-{}'.format(
                             p['name'],
                             p['auths']) for p in profiles()]
                         )
def test_create(shared_client, cleanup, profile, isolated_filesystem):
    """Run a scan on a system and confirm it completes.

    :id: ee3b0bc8-1489-443e-86bb-e2a2349e9c98
    :description: Create a scan and assert that it completes
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
        3) Create a scan
        4) Assert that the scan completes and a fact id is generated
    :expectedresults: A scan is run and has facts associated with it
    """
    cfg = config.get_config()

    auth_ids = []
    for auth in cfg['qcs'].get('auths'):
        if auth['name'] in profile['auths']:
            cred = HostCredential(
                client=shared_client,
                ssh_keyfile=auth['sshkeyfile'],
                username=auth['username'],
            )
            cred.create()
            cleanup.append(cred)
            auth_ids.append(cred._id)

    netprof = NetworkProfile(
        client=shared_client,
        hosts=profile['hosts'],
        credential_ids=auth_ids,
    )
    netprof.create()
    cleanup.append(netprof)
    scan = Scan(source_id=netprof._id)
    scan.create()
    wait_until_complete(scan)
    assert scan.status() == 'completed'
    assert isinstance(scan.read().json().get('fact_collection_id'), int)


@pytest.mark.skip
def test_pause_cancel(shared_client, cleanup, profile, isolated_filesystem):
    """Run a scan on a system and confirm we can pause and cancel it.

    :id: 4d4b9839-1672-4183-bd27-11864787eb8e
    :description: Assert that scans can be paused and then cancelled.
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
        3) Create a scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be canceled
    :expectedresults: A scan can be paused and cancelled
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_restart(shared_client, cleanup, profile, isolated_filesystem):
    """Run a scan on a system and confirm we can pause and restart it.

    :id: 6d81121d-500e-4188-8195-2e469ca606c0
    :description: Assert that scans can be paused and then restarted.
    :steps:
        1) Create host credential
        2) Send POST with data to create network profile using the host
           credential to the profile endpoint.
        3) Create a scan
        4) Assert that the scan can be paused
        5) Assert that the scan can be restarted
        6) Assert that he scan completes
    :expectedresults: A restarted scan completes
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_queue_mix_valid_invalid(
        shared_client,
        cleanup,
        profile,
        isolated_filesystem):
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
    :caseautomation: notautomated
    """
    pass


@pytest.mark.skip
def test_queue_mix_paused_cancelled(
        shared_client,
        cleanup,
        profile,
        isolated_filesystem):
    """Assert all non-cancelled and paused scans in a queue complete.

    :id: 925e2a72-3e69-4947-bfd7-5298bc033963
    :description: Ensure scans can progress in queue that contains paused and
        cancelled scans to completion.
    :steps:
        1) Create a series of valid scans
        2) Pause and cancel a random selection of scans
        3) Assert that all non-paused/cancelled scans complete
        4) Restart the paused scans and assert they complete
        5) Assert the cancelled scans stay cancelled
    :expectedresults: All non-paused/cancelled scans will progress in queue
    :caseautomation: notautomated
    """
    pass
