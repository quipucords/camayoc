# coding=utf-8
"""Shared utility functions for v1 tests."""

import pprint
import time

from camayoc.constants import (
    QPC_SCAN_STATES,
    QPC_SCAN_TERMINAL_STATES,
)
from camayoc.exceptions import (
    FailedScanException,
    WaitTimeError,
)


def wait_until_state(scanjob, timeout=120, state='completed'):
    """Wait until the scanjob has failed or reached desired state.

    The default state is 'completed'.

    Valid options for 'state': 'completed', 'failed', 'paused',
    'canceled', 'running', 'stopped'.

    If 'stopped' is selected, then any state other than 'running' will
    cause `wait_until_state` to return.

    This method should not be called on scanjob jobs that have not yet been
    created, are paused, or are canceled.

    The default timeout is set to 120 seconds, but can be overridden if it is
    anticipated that a scanjob may take longer to complete.
    """
    valid_states = QPC_SCAN_STATES + ('stopped',)
    if state not in valid_states:
        raise ValueError(
            'You have called `wait_until_state` and specified an invalid\n'
            'state={0}. Valid options for "state" are [ {1} ]'.format(
                state,
                pprint.pformat(valid_states),
            )
        )

    while (not scanjob.status() or not scanjob.status()
            == state) and timeout > 0:
        if state == 'stopped' and scanjob.status() in QPC_SCAN_TERMINAL_STATES:
            # scanjob is no longer running, so we will return
            return
        time.sleep(5)
        timeout -= 5
        if timeout <= 0:
            raise WaitTimeError(
                'You have called wait_until_state() on a scanjob with\n'
                'ID={scanjob_id} and the scanjob timed out while waiting\n'
                'to achieve the state="{expected_state}"\n'
                'When the scanjob timed out, it had the'
                ' state="{scanjob_state}".\n'
                'The scanjob was started for the scan with id {scan_id}'
                'The full details of the scanjob were \n{scanjob_details}\n'
                'The "results" available from the scanjob were'
                '\n{scanjob_results}\n'.format(
                    scanjob_id=scanjob._id,
                    scan_id=scanjob.scan_id,
                    expected_state=state,
                    scanjob_state=scanjob.status(),
                    scanjob_details=pprint.pformat(
                        scanjob.read().json()),
                    scanjob_results=pprint.pformat(
                        scanjob.read().json().get('tasks'))))
        if state not in ['stopped', 'failed'] and scanjob.status() == 'failed':
            raise FailedScanException(
                'You have called wait_until_state() on a scanjob with\n'
                'ID={scanjob_id} and the scanjob failed instead of reaching\n'
                'the state="{expected_state}"\n'
                'When the scanjob failed, it had the state="{scanjob_state}".'
                '\nThe scanjob was started for the scan with id {scan_id}'
                'The full details of the scanjob were \n{scanjob_details}\n'
                'The "results" available from the scanjob were \n'
                '{scanjob_results}\n' .format(
                    scanjob_id=scanjob._id,
                    scan_id=scanjob.scan_id,
                    expected_state=state,
                    scanjob_state=scanjob.status(),
                    scanjob_details=pprint.pformat(
                        scanjob.read().json()),
                    scanjob_results=pprint.pformat(
                        scanjob.read().json().get('tasks'))))
