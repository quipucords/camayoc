"""Web user interface end-to-end tests.

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

import pytest

from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import Source
from camayoc.tests.qpc.utils import calculate_sha256sums
from camayoc.tests.qpc.utils import get_expected_sha256sums
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AddCredentialDTOFactory
from camayoc.ui.data_factories import AddSourceDTOFactory
from camayoc.ui.data_factories import SSHNetworkCredentialFormDTOFactory
from camayoc.ui.data_factories import TriggerScanDTOFactory
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import NetworkCredentialBecomeMethods
from camayoc.ui.enums import SourceTypes


def credential_source_pairs():
    credential_form = SSHNetworkCredentialFormDTOFactory(
        username="cloud-user",
        ssh_key_file="/sshkeys/id_rsa",
        passphrase="",
        become_method=NetworkCredentialBecomeMethods.SUDO,
        become_user="root",
        become_password="",
    )
    credential = AddCredentialDTOFactory(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=credential_form,
    )
    source = AddSourceDTOFactory(
        select_source_type__source_type=SourceTypes.NETWORK_RANGE,
        source_form__addresses=["10.0.151.20", "10.0.149.227"],
        source_form__credentials=[credential.credential_form_dto.credential_name],
    )
    yield pytest.param(credential, source, id="network")

    credential = AddCredentialDTOFactory(credential_type=CredentialTypes.SATELLITE)
    source = AddSourceDTOFactory(
        select_source_type__source_type=SourceTypes.SATELLITE,
        source_form__credentials=[credential.credential_form_dto.credential_name],
    )
    yield pytest.param(credential, source, id="satellite")

    credential = AddCredentialDTOFactory(credential_type=CredentialTypes.VCENTER)
    source = AddSourceDTOFactory(
        select_source_type__source_type=SourceTypes.VCENTER_SERVER,
        source_form__credentials=[credential.credential_form_dto.credential_name],
    )
    yield pytest.param(credential, source, id="vcenter")


@pytest.mark.parametrize("credential,source", credential_source_pairs())
def test_end_to_end(cleanup, ui_client: Client, credential, source):
    """End-to-end test using web user interface.

    :id: f187fbd0-021c-4563-9691-61e54eb272bf
    :description: This is end-to-end user journey through web user interface.
    :steps:
        1) Log into the UI.
        2) Go to Credentials page, open Credentials modal and fill in the form.
        3) Go to Sources page, open Sources wizard and fill in all the forms.
        4) Trigger scan for newly created source.
        5) Wait for scan to complete.
        6) Download scan report.
        7) Log out.
    :expectedresults: Credential and Source are created. Scan is completed.
        Report is downloaded. User is logged out.
    """
    trigger_scan_data = TriggerScanDTOFactory(
        source_name=source.source_form.source_name,
        scan_form__jboss_eap=None,
        scan_form__fuse=None,
        scan_form__jboss_web_server=None,
        scan_form__decision_manager=None,
    )
    cleanup.append(Credential(name=credential.credential_form_dto.credential_name))
    cleanup.append(Scan(name=trigger_scan_data.scan_form.scan_name))
    cleanup.append(Source(name=source.source_form.source_name))
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source)
        .trigger_scan(trigger_scan_data)
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(trigger_scan_data.scan_form.scan_name)
        .logout()
    )

    downloaded_report = ui_client.downloaded_files[-1]
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
