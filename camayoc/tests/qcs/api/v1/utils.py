# coding=utf-8
"""Shared utility functions for v1 tests."""

import pprint
import time

from camayoc import config
from camayoc.exceptions import (
    WaitTimeError,
    FailedScanException,
    ConfigFileNotFoundError,
)
from camayoc.constants import (
    QCS_SCAN_STATES,
    QCS_SCAN_TERMINAL_STATES,
)
from camayoc.qcs_models import (
    Credential,
    Source,
    Scan
)


def wait_until_state(scan, timeout=120, state='completed'):
    """Wait until the scan has failed or reached desired state.

    The default state is 'completed'.

    Valid options for 'state': 'completed', 'failed', 'paused',
    'canceled', 'running', 'stopped'.

    If 'stopped' is selected, then any state other than 'running' will
    cause `wait_until_state` to return.

    This method should not be called on scan jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 120 seconds, but can be overridden if it is
    anticipated that a scan may take longer to complete.
    """
    valid_states = QCS_SCAN_STATES + ('stopped',)
    if state not in valid_states:
        raise ValueError(
            'You have called `wait_until_state` and specified an invalid\n'
            'state={0}. Valid options for "state" are [ {1} ]'.format(
                state,
                pprint.pformat(valid_states),
            )
        )

    while (
            not scan.status() or not scan.status() == state) and timeout > 0:
        if state == 'stopped' and scan.status() in QCS_SCAN_TERMINAL_STATES:
            # scan is no longer running, so we will return
            return
        time.sleep(5)
        timeout -= 5
        if timeout <= 0:
            raise WaitTimeError(
                'You have called wait_until_state() on a scan with ID={} and\n'
                'the scan timed out while waiting to achieve the state="{}"\n'
                'When the scan timed out, it had the state="{}".\n'
                'The full details of the scan were \n{}\n'
                'The "results" available from the scan were \n{}\n'
                .format(
                    scan._id,
                    state,
                    scan.status(),
                    pprint.pformat(scan.read().json()),
                    pprint.pformat(scan.results().json()),
                )
            )
        if state not in ['stopped', 'failed'] and scan.status() == 'failed':
            raise FailedScanException(
                'You have called wait_until_state() on a scan with ID={} and\n'
                'the scan failed instead of acheiving state={}.\n'
                'When it failed, the details about the scan were \n{}\n'
                'The "results" available from the scan were \n{}\n'
                .format(
                    scan._id,
                    state,
                    pprint.pformat(scan.read().json()),
                    pprint.pformat(scan.results().json()),
                )
            )


def all_sources():
    """Gather sources from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no sources are found.
    """
    try:
        srcs = [s for s in config.get_config()['qcs']['sources']]
    except (ConfigFileNotFoundError, KeyError):
        srcs = []
    return srcs


def network_sources():
    """Gather sources from config file.

    If no config file is found, or no sources defined,
    then an empty list will be returned.

    If a test is parametrized on the sources in the config file, it will skip
    if no sources are found.
    """
    try:
        srcs = [s for s in config.get_config()['qcs']['sources']
                if s['type'] == 'network']
    except (ConfigFileNotFoundError, KeyError):
        srcs = []
    return srcs


def first_network_source():
    """Gather sources from config file.

    If no source is found in the config file, or no config file is found, a
    default source will be returned.
    """
    try:
        for s in config.get_config()['qcs']['sources']:
            if s['type'] == 'network':
                src = [s]
                break
    except (ConfigFileNotFoundError, KeyError):
        src = [
            {
                'hosts': ['localhost'],
                'name':'localhost',
                'credentials':'root'
            }
        ]
    return src


def prep_broken_scan(source_type, cleanup, scan_type='inspect'):
    """Return a scan that can be created but will fail to complete.

    Create and return a source with a non-existent host and dummy credential.
    It is returned ready to be POSTed to the server via the create() instance
    method.
    """
    bad_cred = Credential(
        username='broken',
        password='broken',
        cred_type=source_type
    )
    bad_cred.create()
    cleanup.append(bad_cred)
    bad_src = Source(
        source_type=source_type,
        hosts=['1.0.0.0'],
        credential_ids=[bad_cred._id],
    )
    bad_src.create()
    cleanup.append(bad_src)
    bad_scn = Scan(
        source_ids=[bad_src._id],
        scan_type=scan_type,
    )
    return bad_scn


def prep_network_scan(source, cleanup, client, scan_type='inspect'):
    """Given a source from config file, prep the scan.

    Takes care of creating the Credential and Source objects on the server and
    staging them for cleanup after the tests complete.
    """
    cfg = config.get_config()
    cred_ids = []
    for c in cfg['credentials']:
        if c['name'] in source['credentials'] and c['type'] == 'network':
            cred = Credential(
                cred_type='network',
                client=client,
                username=c['username'],
            )
            if c.get('sshkeyfile'):
                cred.ssh_keyfile = c['sshkeyfile']
            else:
                cred.password = c['password']
            cred.create()
            cleanup.append(cred)
            cred_ids.append(cred._id)

    netsrc = Source(
        source_type='network',
        client=client,
        hosts=source['hosts'],
        credential_ids=cred_ids,
    )
    netsrc.create()
    cleanup.append(netsrc)
    scan = Scan(source_ids=[netsrc._id], scan_type=scan_type)
    return scan


def prep_all_source_scan(cleanup, client, scan_type='inspect'):
    """Prep a scan that scans every source listed in the config file.

    Takes care of creating the Credential and Source objects on the server and
    staging them for cleanup after the tests complete.
    """
    cfg = config.get_config()
    creds = {}
    for c in cfg['credentials']:
        cred = Credential(
            cred_type=c['type'],
            client=client,
            username=c['username'],
        )
        if c.get('sshkeyfile'):
            cred.ssh_keyfile = c['sshkeyfile']
        else:
            cred.password = c['password']
        cred.create()
        cleanup.append(cred)
        creds[c['name']] = cred._id

    all_sources = []
    for s in cfg['qcs']['sources']:
        src = Source(
            source_type=s['type'],
            client=client,
            hosts=s['hosts'],
            credential_ids=[creds[s['credentials'][0]]],
            options=s.get('options')
        )
        src.create()
        all_sources.append(src._id)
        cleanup.append(src)

    scan = Scan(source_ids=all_sources, scan_type=scan_type)
    return scan
