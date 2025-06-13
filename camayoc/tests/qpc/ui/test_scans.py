"""Web user interface scan tests.

:caseautomation: automated
:casecomponent: ui
:caseimportance: medium
:caselevel: integration
:testtype: functional
"""

import tarfile

import pytest

from camayoc.config import settings
from camayoc.tests.qpc.utils import assert_ansible_logs
from camayoc.tests.qpc.utils import assert_sha256sums
from camayoc.types.ui import SummaryReportData
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import ColumnOrdering
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import ScansModalTableColumns

SUMMARY_RESULTS_ITEMS = (
    "ansible_hosts_all",
    "instances_hypervisor",
    "instances_physical",
    "instances_virtual",
    "openshift_cores",
    "socket_pairs",
    "system_creation_date_average",
    "vmware_hosts",
)
SUMMARY_DIAGNOSTICS_ITEMS = (
    "inspect_result_status_failed",
    "inspect_result_status_success",
    "inspect_result_status_unknown",
    "inspect_result_status_unreachable",
    "missing_pem_files",
    "missing_system_creation_date",
    "missing_system_purpose",
)


def has_network_source(scan_name):
    network_sources = set([source.name for source in settings.sources if source.type == "network"])
    for scan_definition in settings.scans:
        if scan_definition.name != scan_name:
            continue
        scan_sources = set(scan_definition.sources)
        return bool(network_sources.intersection(scan_sources))
    return False


def scan_names():
    for scan_definition in settings.scans:
        yield pytest.param(scan_definition.name)


@pytest.mark.pr_only
@pytest.mark.parametrize("scan_name", scan_names())
def test_download_scan(tmp_path, scans, ui_client: Client, scan_name):
    """Download finished scan and verify basic content properties.

    :id: 66abf967-24f1-43cb-9375-c1a5e519a0e6
    :description: This is the last part of end-to-end user journey through web
        user interface. It is split out from end_to_end test to allow usage of
        cached scans results.
    :steps:
        1) Log into the UI.
        2) Download finished scan report.
        3) Verify downloaded file looks like a valid scan.
        4) Log out.
    :expectedresults: Report is downloaded. User is logged out.
    """
    finished_scan = scans.with_name(scan_name)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(finished_scan.definition.name)
        .logout()
    )

    is_network_scan = has_network_source(scan_name)
    downloaded_report = ui_client.downloaded_files[-1]

    tarfile.open(downloaded_report.path()).extractall(tmp_path)
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)


@pytest.mark.nightly_only
@pytest.mark.parametrize("scan_name", scan_names())
def test_download_scan_modal(tmp_path, scans, ui_client: Client, scan_name):
    """Download finished scan using modal and verify basic content properties.

    :id: 00fc7f4f-6f7a-4947-869e-749060a2285f
    :description: This is almost exact copy of test_download_scan, except
        this one clicks button in "Last scanned" column and uses modal
        to download the scan results.
    :steps:
        1) Log into the UI.
        2) Download finished scan report using the modal.
        3) Verify downloaded file looks like a valid scan.
        4) Log out.
    :expectedresults: Report is downloaded. User is logged out.
    """
    finished_scan = scans.with_name(scan_name)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SCANS)
        .download_scan_modal(
            finished_scan.definition.name,
            ScansModalTableColumns.SCAN_TIME,
            ColumnOrdering.DESCENDING,
            0,
        )
        .logout()
    )

    is_network_scan = has_network_source(scan_name)
    downloaded_report = ui_client.downloaded_files[-1]

    tarfile.open(downloaded_report.path()).extractall(tmp_path)
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)


@pytest.mark.parametrize("scan_name", scan_names())
def test_show_summary_report(scans, ui_client: Client, scan_name):
    """Open summary report modal and verify it displays correct data.

    :id: e57252ad-1c4a-406f-91d3-bc8d948d82c0
    :description: Open modal with a summary report and confirm data
        matches API response. In standard user flow, we expect summary
        to act as quick check of correctness before downloading a full
        report.
    :steps:
        1) Log into the UI.
        2) Open modal with Summary report for finished scan.
        3) Verify displayed data matches API response.
        4) Log out.
    :expectedresults: Data in UI matches data from API. User is logged out.
    """
    finished_scan = scans.with_name(scan_name)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SCANS)
        .read_summary_modal(finished_scan.definition.name)
        .logout()
    )
    ui_summary_report: SummaryReportData = ui_client.page_contents[-1]

    for key in SUMMARY_RESULTS_ITEMS:
        reference = finished_scan.aggregate_report.get("results", {}).get(key)
        actual = ui_summary_report.get(key)
        assert reference == actual.parsed_value

    for key in SUMMARY_DIAGNOSTICS_ITEMS:
        reference = finished_scan.aggregate_report.get("diagnostics", {}).get(key)
        actual = ui_summary_report.get(key)
        assert reference == actual.parsed_value
