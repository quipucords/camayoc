# coding=utf-8
"""Shared utility functions for v1 tests."""

import pprint
import time

from camayoc.constants import QPC_SCAN_STATES
from camayoc.constants import QPC_SCAN_TERMINAL_STATES
from camayoc.exceptions import StoppedScanException
from camayoc.exceptions import WaitTimeError
from camayoc.qpc_models import Scan


def get_source(source_type, cleanup):
    """Retrieve a single network source if available from config file.

    :param source_type: The type of source to be created. This function
        retreives one source of matching type from the config file.

    :param cleanup: The "cleanup" list that tests use to destroy objects after
        a test has run. The "cleanup" list is provided by the py.test fixture
        of the same name defined in camayoc/tests/qpc/conftest.py.

    Sources are retreived from the following section and are assumed to be
    available on demand and do not require their power state to be managed.
    The expected configuration in the Camayoc's configuration file is as
    follows::

        qpc:
        # other needed qpc config data
            sources:
                 - hosts:
                       - '127.0.0.1'
                   name: local
                   type: network
                   credentials:
                       - root

    The credential listed is assumed to be in the top level 'credentials'
    section.

    This source is meant to be used for tests where we do not care about the
    results of the scan, for example tests that assert we can pause and restart
    a scan.

    :returns: camayoc.qpc_models.Source of the same type that was requested
        with the 'source_type' parameter. The returned source has been created
        on server and has all credentials listed in config file created and
        associtated with it.
    """
    # FIXME: Taking some debt here. This function is only used by prepare_scan, which in
    # turn is only used by 2 tests that are skipped. These tests should be rewritten to
    # data_provider, which fundamentally does exactly the same thing.
    return None


def prepare_scan(source_type, cleanup):
    """Prepare a scan from the 'sources' section of config file.

    :param source_type: The scan will be configured to use one source, of the
        type specified with this parameter. Uses ``get_network_source`` to
        retreive a source of this type from the config file.

    :param cleanup: The "cleanup" list that tests use to destroy objects after
        a test has run. The "cleanup" list is provided by the py.test fixture
        of the same name defined in camayoc/tests/qpc/conftest.py.

    This scan is not meant for testing the results of the scan, rather for
    functional tests that test the ability to effect the state of the scan,
    for example if you can restart a paused scan.

    :returns: camayoc.qpc_models.Scan configured for the network source found
       in the config file.
    """
    src = get_source(source_type, cleanup)
    if not src:
        return
    scn = Scan(scan_type="inspect", source_ids=[src._id])
    scn.create()
    cleanup.append(scn)
    return scn


def wait_until_state(scanjob, timeout=3600, state="completed"):
    """Wait until the scanjob has failed or reached desired state.

    The default state is 'completed'.

    Valid options for 'state': 'completed', 'failed', 'paused',
    'canceled', 'running', 'stopped'.

    If 'stopped' is selected, then any state other than 'running' will
    cause `wait_until_state` to return.

    This method should not be called on scanjob jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 3600 seconds (an hour), but can be
    overridden. An hour is an extremely long time. We use this because
    it is been proven that in general the server is accurate when
    reporting that a task really is still running. All other terminal
    states will cause this function to return.
    """
    valid_states = QPC_SCAN_STATES + ("stopped",)
    stopped_states = QPC_SCAN_TERMINAL_STATES + ("stopped",)
    if state not in valid_states:
        raise ValueError(
            "You have called `wait_until_state` and specified an invalid\n"
            'state={0}. Valid options for "state" are [ {1} ]'.format(
                state, pprint.pformat(valid_states)
            )
        )

    current_status = scanjob.status()
    while True:
        # achieved expected state - happy path
        if current_status == state:
            return

        # scanjob is no longer running, user wanted one of stopped states. Stopped is stopped
        if current_status in stopped_states and state in stopped_states:
            return

        scanjob_details = scanjob.read().json()
        exception_format = {
            "scanjob_id": scanjob._id,
            "scan_id": scanjob.scan_id,
            "expected_state": state,
            "scanjob_state": current_status,
            "scanjob_details": pprint.pformat(scanjob_details),
            "scanjob_results": pprint.pformat(scanjob_details.get("tasks")),
        }

        if current_status in stopped_states and state not in stopped_states:
            raise StoppedScanException(
                "You have called wait_until_state() on a scanjob with\n"
                "ID={scanjob_id} has stopped running instead of reaching \n"
                'the state="{expected_state}"\n'
                'When the scanjob stopped, it had the state="{scanjob_state}".'
                "\nThe scanjob was started for the scan with id {scan_id}"
                "The full details of the scanjob were \n{scanjob_details}\n"
                'The "results" available from the scanjob were \n'
                "{scanjob_results}\n".format(**exception_format)
            )

        if timeout <= 0:
            raise WaitTimeError(
                "You have called wait_until_state() on a scanjob with\n"
                "ID={scanjob_id} and the scanjob timed out while waiting\n"
                'to achieve the state="{expected_state}"\n'
                "When the scanjob timed out, it had the"
                ' state="{scanjob_state}".\n'
                "The scanjob was started for the scan with id {scan_id}"
                "The full details of the scanjob were \n{scanjob_details}\n"
                'The "results" available from the scanjob were'
                "\n{scanjob_results}\n".format(**exception_format)
            )

        time.sleep(5)
        timeout -= 5
        current_status = scanjob.status()
