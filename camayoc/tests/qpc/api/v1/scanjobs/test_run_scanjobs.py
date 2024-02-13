# coding=utf-8
"""Tests for quipucords scanjobs.

These tests are parametrized on the inventory listed in the config file.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
from pprint import pformat

import pytest

from camayoc import utils
from camayoc.tests.qpc.api.v1.conftest import scan_list
from camayoc.types.settings import ScanOptions


@pytest.mark.skip(reason="Test is flaky. Skipping until Quipucords Issue #2040 resoloved")
@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_scan_complete(scan_info: ScanOptions):
    """Test that each scan completed without failures.

    :id: 4e7a608e-a18d-48db-b263-a0d5474385dd
    :description: Test if the scan completed.
    :steps: Check the final status of the scan.
    :expectedresults: Scans should complete and report their finished status.
    """

    def get_scan_result(scan_name):
        return {}

    result = get_scan_result(scan_info.name)
    if result["final_status"] != "completed":
        raise AssertionError(
            "Scan did not complete. Its final status was {status}.\n"
            " NOTE: A scan will be reported as failed if there were\n"
            " unreachable hosts.\n"
            " ============================================================\n"
            " Any additional HTTP errors encountered while attempting\n"
            " to run the scan are listed here: \n"
            "{errors}\n"
            " ============================================================\n"
            " Details from the scan including scan_id, scan_job_id, and the\n"
            "inspeciton results:\n"
            "{results}\n".format(
                status=result["final_status"],
                errors="\n".join(result["errors"]),
                results=pformat(result),
            )
        )
