# coding=utf-8
"""Tests for quipucords scanjobs.

These tests are parametrized on the inventory listed in the config file.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import pytest

from camayoc.tests.qpc.utils import all_scan_names
from camayoc.types.scans import ScanSimplifiedStatusEnum


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", all_scan_names())
def test_scan_complete(scans, scan_name):
    """Test that each scan completed without failures.

    :id: 4e7a608e-a18d-48db-b263-a0d5474385dd
    :description: Test if the scan completed.
    :steps: Check the final status of the scan.
    :expectedresults: Scans should complete and report their finished status.
    """
    all_scans = scans.all()
    finished_scan = all_scans.get(scan_name)
    assert finished_scan.status == ScanSimplifiedStatusEnum.COMPLETED, (
        "Scan did not complete. Its final status was {status}.\n"
        " NOTE: A scan will be reported as failed if there were\n"
        " unreachable hosts.\n"
        " ============================================================\n"
        " Scan name: {scan_name}\n"
        " Scan id: {scan_id}\n"
        " Scan job id: {scanjob_id}\n"
        " Encountered exception: {error}\n".format(
            status=finished_scan.status,
            scan_name=finished_scan.definition.name,
            scan_id=finished_scan.scan_id,
            scanjob_id=finished_scan.scan_job_id,
            error=finished_scan.error,
        )
    )
