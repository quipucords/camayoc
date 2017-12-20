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
from camayoc.exceptions import ConfigFileNotFoundError, WaitTimeError
from camayoc.qcs_models import (
    Credential,
    Source,
    Scan,
)


def sources():
    """Gather sources from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no sources are found.
    """
    try:
        srcs = config.get_config()['qcs']['sources']
    except (ConfigFileNotFoundError, KeyError):
        srcs = []
    return srcs


def first_source():
    """Gather sources from config file.

    If no source is found in the config file, or no config file is found, a
    default source will be returned.
    """
    try:
        src = [config.get_config()['qcs']['sources'][0]]
    except (ConfigFileNotFoundError, KeyError):
        src = [{'hosts': ['localhost'], 'name':'localhost', 'auths':'default'}]
    return src


def wait_until_state(scan, timeout=120, state='completed'):
    """Wait until the scan has failed or reached desired state.

    The default state is 'completed'.

    This method should not be called on scan jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 120 seconds, but can be overridden if it is
    anticipated that a scan may take longer to complete.
    """
    while (
        not scan.status() or not scan.status() in [
            'failed',
            state]) and timeout > 0:
        time.sleep(5)
        timeout -= 5
        if timeout <= 0:
            raise WaitTimeError(
                'You have called wait_until_state() on a scan and the scan\n'
                'timed out while waiting to achieve the state="{}" When the\n'
                'scan timed out, it had the state="{}".\n'
                .format(state, scan.status())
            )


def prep_broken_network_scan(cleanup):
    """Return a scan that can be created but will fail to complete.

    Create and return a source with a non-existent host and dummy credential.
    It is returned ready to be POSTed to the server via the create() instance
    method.
    """
    bad_cred = Credential(
        username='broken',
        password='broken',
        cred_type='network'
    )
    bad_cred.create()
    cleanup.append(bad_cred)
    bad_src = Source(
        source_type='network',
        hosts=['1.0.0.0'],
        credential_ids=[bad_cred._id],
    )
    bad_src.create()
    cleanup.append(bad_src)
    bad_scn = Scan(
        source_ids=[bad_src._id],
    )
    return bad_scn


def prep_network_scan(source, cleanup, client):
    """Given a source from config file, prep the scan.

    Takes care of creating the Credential and Source objects on the server and
    staging them for cleanup after the tests complete.
    """
    cfg = config.get_config()
    auth_ids = []
    for auth in cfg['qcs'].get('auths'):
        if auth['name'] in source['auths']:
            cred = Credential(
                cred_type='network',
                client=client,
                ssh_keyfile=auth['sshkeyfile'],
                username=auth['username'],
            )
            cred.create()
            cleanup.append(cred)
            auth_ids.append(cred._id)

    netsrc = Source(
        source_type='network',
        client=client,
        hosts=source['hosts'],
        credential_ids=auth_ids,
    )
    netsrc.create()
    cleanup.append(netsrc)
    scan = Scan(source_ids=[netsrc._id])
    return scan


@pytest.mark.parametrize('source', sources(), ids=[
                         '{}-{}'.format(
                             s['name'],
                             s['auths']) for s in sources()]
                         )
def test_create(shared_client, cleanup, source, isolated_filesystem):
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
    """
    scan = prep_network_scan(source, cleanup, shared_client)
    scan.create()
    wait_until_state(scan)
    assert scan.status() == 'completed'
    assert isinstance(scan.read().json().get('fact_collection_id'), int)


@pytest.mark.parametrize('source', first_source(), ids=[
                         '{}-{}'.format(
                             first_source()[0]['name'],
                             first_source()[0]['auths'])]
                         )
def test_pause_cancel(shared_client, cleanup, source, isolated_filesystem):
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


@pytest.mark.parametrize('source', first_source(), ids=[
                         '{}-{}'.format(
                             first_source()[0]['name'],
                             first_source()[0]['auths'])]
                         )
def test_restart(shared_client, cleanup, source, isolated_filesystem):
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


@pytest.mark.parametrize('source', first_source(), ids=[
                         '{}-{}'.format(
                             first_source()[0]['name'],
                             first_source()[0]['auths'])]
                         )
def test_queue_mix_valid_invalid(
        shared_client,
        cleanup,
        source,
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
    """
    good_scans = []
    bad_scans = []
    for k in range(6):
        time.sleep(2)
        if not k % 2:
            bad_scn = prep_broken_network_scan(cleanup)
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
        assert scan.status() == 'failed'


@pytest.mark.parametrize('source', first_source(), ids=[
                         '{}-{}'.format(
                             first_source()[0]['name'],
                             first_source()[0]['auths'])]
                         )
def test_queue_mix_paused_canceled(
        shared_client,
        cleanup,
        source,
        isolated_filesystem):
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

    for scan in paused_scans:
        assert scan.status() == 'paused'
        scan.cancel()

    for scan in paused_scans:
        assert scan.status() == 'canceled'
