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
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import MainMenuPages


def has_network_source(scan_name):
    network_sources = set([source.name for source in settings.sources if source.type == "network"])
    for scan_definition in settings.scans:
        if scan_definition.name != scan_name:
            continue
        scan_sources = set(scan_definition.sources)
        return bool(network_sources.intersection(scan_sources))


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
