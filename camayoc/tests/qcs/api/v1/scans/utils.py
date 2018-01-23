# coding=utf-8
"""Shared utility functions for scan tests."""

import pprint
import time

from camayoc.qcs_models import (
    Credential,
    Source,
    Scan
)
from camayoc.exceptions import WaitTimeError, FailedScanException


def wait_until_state(scan, timeout=120, state='completed'):
    """Wait until the scan has failed or reached desired state.

    The default state is 'completed'.

    This method should not be called on scan jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 120 seconds, but can be overridden if it is
    anticipated that a scan may take longer to complete.
    """
    while (
            not scan.status() or not scan.status() == state) and timeout > 0:
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
        if state != 'failed' and scan.status() == 'failed':
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


def prep_broken_scan(scan_type, cleanup):
    """Return a scan that can be created but will fail to complete.

    Create and return a source with a non-existent host and dummy credential.
    It is returned ready to be POSTed to the server via the create() instance
    method.
    """
    bad_cred = Credential(
        username='broken',
        password='broken',
        cred_type=scan_type
    )
    bad_cred.create()
    cleanup.append(bad_cred)
    bad_src = Source(
        source_type=scan_type,
        hosts=['1.0.0.0'],
        credential_ids=[bad_cred._id],
    )
    bad_src.create()
    cleanup.append(bad_src)
    bad_scn = Scan(
        source_ids=[bad_src._id],
    )
    return bad_scn