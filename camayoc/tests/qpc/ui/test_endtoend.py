"""Web user interface end-to-end tests.

:caseautomation: automated
:casecomponent: ui
:caseimportance: medium
:caselevel: integration
:testtype: functional
"""

import random
import tarfile

import pytest

from camayoc.config import settings
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.utils import assert_ansible_logs
from camayoc.tests.qpc.utils import assert_sha256sums
from camayoc.types.ui import AddCredentialDTO
from camayoc.types.ui import AddSourceDTO
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import TriggerScanDTOFactory
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import SourceTypes


def create_endtoend_dtos(source_name, data_provider):
    known_sources_map = {
        source_definition.name: source_definition for source_definition in settings.sources
    }
    source_definition = known_sources_map.get(source_name)
    credential_name = random.choice(source_definition.credentials)
    credential_model = data_provider.credentials.new_one({"name": credential_name}, data_only=True)
    credential_dto = AddCredentialDTO.from_model(credential_model)

    source_model = data_provider.sources.new_one(
        {"name": source_definition.name}, new_dependencies=True, data_only=True
    )
    source_model.credentials = [credential_model.name]
    source_dto = AddSourceDTO.from_model(source_model)

    trigger_scan_dto = TriggerScanDTOFactory(
        source_name=source_model.name,
        scan_form__jboss_eap=None,
        scan_form__fuse=None,
        scan_form__jboss_web_server=None,
    )
    data_provider.mark_for_cleanup(
        credential_model, source_model, Scan(name=trigger_scan_dto.scan_form.scan_name)
    )
    return credential_dto, source_dto, trigger_scan_dto


def source_names():
    for source_definition in settings.sources:
        if source_definition.type in ("openshift",):
            continue
        fixture_id = f"{source_definition.name}-{source_definition.type}"
        yield pytest.param(source_definition.name, id=fixture_id)


@pytest.mark.nightly_only
@pytest.mark.parametrize("source_name", source_names())
def test_end_to_end(tmp_path, cleaning_data_provider, ui_client: Client, source_name):
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
    credential_dto, source_dto, trigger_scan_dto = create_endtoend_dtos(
        source_name, cleaning_data_provider
    )
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .trigger_scan(trigger_scan_dto)
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(trigger_scan_dto.scan_form.scan_name)
        .logout()
    )

    is_network_scan = source_dto.select_source_type.source_type == SourceTypes.NETWORK_RANGE
    downloaded_report = ui_client.downloaded_files[-1]

    tarfile.open(downloaded_report.path()).extractall(tmp_path)
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)


@pytest.mark.skip("Skipped due to intermittent failure - DISCOVERY-426")
@pytest.mark.parametrize("source_name", source_names())
def test_trigger_scan(cleaning_data_provider, ui_client: Client, source_name):
    """Mostly end-to-end test using web user interface (without downloading scan results).

    :id: ae8b2d7d-8ac2-4957-a67a-6dedd80f4f31
    :description: This is mostly end-to-end user journey through the web user interface.
        To save time, we don't wait for scan to complete and we don't download scan
        results.
    :steps:
        1) Log into the UI.
        2) Go to Credentials page, open Credentials modal and fill in the form.
        3) Go to Sources page, open Sources wizard and fill in all the forms.
        4) Trigger scan for newly created source.
        5) Verify that scan has started.
        6) Log out.
    :expectedresults: Credential and Source are created. Scan has started.
        User is logged out.
    """
    credential_dto, source_dto, trigger_scan_dto = create_endtoend_dtos(
        source_name, cleaning_data_provider
    )
    scans_page = (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .trigger_scan(trigger_scan_dto)
        .navigate_to(MainMenuPages.SCANS)
    )
    assert scans_page._get_item(trigger_scan_dto.scan_form.scan_name).locator.is_visible()
