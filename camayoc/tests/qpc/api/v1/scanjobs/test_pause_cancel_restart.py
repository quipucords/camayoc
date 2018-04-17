# coding=utf-8
"""Tests for  quipucords scans and reports.

These tests are parametrized on QCS_SOURCE_TYPES. If no source is availble of a
type in the config file, the test will skip.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: quipucords
:testtype: functional
:upstream: yes
"""
import pytest

import camayoc.tests.qpc.api.v1.utils as util
from camayoc.constants import QPC_SOURCE_TYPES
from camayoc.qpc_models import ScanJob
from camayoc.tests.qpc.utils import mark_runs_scans


@mark_runs_scans
@pytest.mark.parametrize('source_type', QPC_SOURCE_TYPES)
def test_pause_cancel(shared_client, cleanup, source_type):
    """Run a scan on a system and confirm we can pause and cancel it.

    :id: 4d4b9839-1672-4183-bd27-11864787eb8e
    :description: Assert that scans can be paused and then canceled.
    :steps:
        1) Create necessary credentials and sources
        2) Create the scan configuration
        3) Create a scan job
        4) Assert that the scan can be paused
        5) Assert that the scan can be canceled
    :expectedresults: A scan can be paused and canceled
    """
    scn = util.prepare_scan(source_type, cleanup)
    if not scn:
        pytest.skip(
            'No {0} type source was found in the config file.'
            .format(source_type)
        )
    job = ScanJob(scan_id=scn._id)
    job.create()
    util.wait_until_state(job, state='running', TIMEOUT=60)
    job.pause()
    util.wait_until_state(job, state='running', TIMEOUT=60)
    job.cancel()
    util.wait_until_state(job, state='canceled', TIMEOUT=60)


@mark_runs_scans
@pytest.mark.parametrize('source_type', QPC_SOURCE_TYPES)
def test_restart(shared_client, cleanup, source_type):
    """Run a scan on a system and confirm we can pause and restart it.

    :id: 6d81121d-500e-4188-8195-2e469ca606c0
    :description: Assert that scans can be paused and then restarted.
    :steps:
        1) Create necessary credentials and sources
        2) Create the scan configuration
        3) Create a scan job
        4) Assert that the scan can be paused
        5) Assert that the scan can be restarted
        6) Assert that the scan completes
    :expectedresults: A restarted scan completes
    """
    scn = util.prepare_scan(source_type, cleanup)
    if not scn:
        pytest.skip(
            'No {0} type source was found in the config file.'
            .format(source_type)
        )
    job = ScanJob(scan_id=scn._id)
    job.create()
    util.wait_until_state(job, state='running', TIMEOUT=60)
    job.pause()
    util.wait_until_state(job, state='running', TIMEOUT=60)
    job.restart()
    util.wait_until_state(job, state='completed')
