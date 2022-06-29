"""Tests for handling credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: medium
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from camayoc.ui import Client
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import NetworkCredentialBecomeMethods
from camayoc.ui.enums import SourceTypes
from camayoc.ui.types import AddCredentialDTO
from camayoc.ui.types import AddSourceDTO
from camayoc.ui.types import LoginFormDTO
from camayoc.ui.types import NetworkSourceFormDTO
from camayoc.ui.types import NewScanFormDTO
from camayoc.ui.types import SelectSourceDTO
from camayoc.ui.types import SSHNetworkCredentialFormDTO
from camayoc.ui.types import TriggerScanDTO
from camayoc.utils import uuid4


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
    credential_name = "my credential name " + uuid4()
    source_name = "my source name " + uuid4()
    scan_name = "my scan name " + uuid4()
    credential_data = AddCredentialDTO(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=SSHNetworkCredentialFormDTO(
            credential_name=credential_name,
            username="my user name" + uuid4(),
            ssh_key_file="/root/.bashrc",
            passphrase="mypassphrase" + uuid4(),
            become_method=NetworkCredentialBecomeMethods.PFEXEC,
            become_user=uuid4().translate({ord(c): None for c in "0123456789-"}),
            become_password="mybecomepassword" + uuid4(),
        ),
    )
    source_data = AddSourceDTO(
        select_source_type=SelectSourceDTO(
            source_type=SourceTypes.NETWORK_RANGE,
        ),
        source_form=NetworkSourceFormDTO(
            name=source_name,
            addresses="192.168.0.1/24",
            credentials=[credential_name],
        ),
    )
    trigger_scan_data = TriggerScanDTO(
        source_name=source_name,
        scan_form=NewScanFormDTO(
            name=scan_name,
            fuse=True,
        ),
    )

    (
        ui_client.begin()
        .login(LoginFormDTO())
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
        .login(LoginFormDTO())
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(scan_name)
    )
    downloaded_report = ui_client.downloaded_files[-1]
    assert "playwright" in downloaded_report.path().as_posix()
    # downloaded_report.path() - Path() object pointing to file on local fs
    # downloaded_report.suggested_filename - str representing how server wants file to be named
    # the workflow from now could be:
    # 1. copy file to some directory we have control over
    # 2. use `tarfile` to unpack files
    # 3. use `json` and `csv` to read unpacked files and assert their content
