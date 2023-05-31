"""Tests that demonstrate capabilities of Playwright-based UI framework.

:caseautomation: automated
:casecomponent: ui
:caseimportance: medium
:caselevel: integration
:testtype: functional
:upstream: yes
"""
import shutil
import tarfile
import tempfile
from pathlib import Path

from camayoc.tests.qpc.utils import calculate_sha256sums
from camayoc.tests.qpc.utils import get_expected_sha256sums
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AddCredentialDTOFactory
from camayoc.ui.data_factories import AddSourceDTOFactory
from camayoc.ui.data_factories import TriggerScanDTOFactory
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import SourceTypes


def test_demo_endtoend(ui_client: Client):
    """Demonstrate new UI framework capabilities in scope of creating data

    :id: 18977f91-700d-4358-975e-f68c0a1c1907
    :description: This demonstrates how you can use DTOs and
        fluent page object pattern to model user journey through
        the system - login, create credential, create source
        associated with this credential and trigger the scan.
        Scan will not succeed.
    :steps:
        1) Log into the UI.
        2) Go to Credentials page, open Credentials modal and fill in the form.
        3) Go to Sources page, open Sources wizard and fill in all the forms.
        4) Trigger scan for newly created source.
    :expectedresults: Credential and Source are created
    """
    import random

    matching_types = [
        (CredentialTypes.NETWORK, SourceTypes.NETWORK_RANGE),
        (CredentialTypes.SATELLITE, SourceTypes.SATELLITE),
        (CredentialTypes.VCENTER, SourceTypes.VCENTER_SERVER),
    ]
    credential_type, source_type = random.choice(matching_types)
    # FIXME: above should be somewhere else

    credential_data = AddCredentialDTOFactory(credential_type=credential_type)
    source_data = AddSourceDTOFactory(
        select_source_type__source_type=source_type,
        source_form__credentials=[credential_data.credential_form_dto.credential_name],
    )
    trigger_scan_data = TriggerScanDTOFactory(
        source_name=source_data.source_form.source_name,
    )

    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_data)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_data)
        .trigger_scan(trigger_scan_data)
        .navigate_to(MainMenuPages.SCANS)
    )


def test_demo_download(ui_client: Client):
    """Demonstrate new UI framework capabilities in scope of downloading data

    :id: c5db7b18-64c8-4646-aed7-febc1261a9d9
    :description: This demonstrates how you can download the file
        and use it later in the test.
    :steps:
        1) Log into the UI.
        2) Go to Scans page and download report of specific scan.
        3) Do something with downloaded file.
    :expectedresults: File is downloaded
    """
    scan_name = "6c0584fd-d092-46a8-afe8-0603663cbcd1"

    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(scan_name)
    )
    downloaded_report = ui_client.downloaded_files[-1]
    assert "playwright" in downloaded_report.path().as_posix()

    report_directory = Path(tempfile.mkdtemp(prefix="camayoc"))
    report_file = report_directory / downloaded_report.suggested_filename
    shutil.copy(downloaded_report.path(), report_file)
    tarfile.open(report_file).extractall(report_directory)
    actual_shasums = calculate_sha256sums(report_directory)
    expected_shasums = get_expected_sha256sums(report_directory)

    for filename, expected_shasum in expected_shasums.items():
        actual_shasum = actual_shasums.get(filename)
        assert actual_shasum == expected_shasum

    for file in report_directory.rglob("*"):
        if not file.is_file():
            continue
        assert file.stat().st_size > 0
