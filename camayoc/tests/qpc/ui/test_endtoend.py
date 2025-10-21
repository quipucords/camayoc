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
from camayoc.tests.qpc.utils import end_to_end_sources_names
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


@pytest.mark.slow
@pytest.mark.nightly_only
@pytest.mark.parametrize("source_name", end_to_end_sources_names())
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

    is_network_scan = source_dto.source_type == SourceTypes.NETWORK_RANGE
    downloaded_report = ui_client.downloaded_files[-1]

    tarfile.open(downloaded_report.path()).extractall(tmp_path)
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)


def test_translations(ui_client: Client):
    """Test that translations are correctly loaded.

    :id: 56248920-f838-4e10-81b7-7d7dc45b65c4
    :description: Verify that translations are loaded and not completely broken.
    :steps:
        1) Log into the UI.
        2) Read static content from Overview page.
        3) Interact with FAQ section on Overview page.
        4) Go to Sources page.
        5) Assert text displayed in "Refresh" button.
        6) Log out.
    :expectedresults: All the static text is translated. User is logged out.
    """
    products = ("Discovery", "Quipucords")
    key_process_text = (
        "To use {product}, first configure credentials to securely access your systems."
        " Then add sources, such as hostnames or IP ranges. With credentials and sources"
        " in place, you can run scans to collect system data and gain insights into your"
        " environment without sharing sensitive information unless you choose to."
    )
    faq_answer_text = (
        "No, {product} does not automatically send any data to Red Hat."
        " All data is stored locally and creates reports on the local file system."
    )

    page = (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.OVERVIEW)
    )

    key_process = page._driver.locator(
        "div[data-ouia-component-id=MultiContentCard-content-2] div[class*=card__body] div"
    ).nth(1)
    assert key_process.inner_text() in [
        key_process_text.format(product=product) for product in products
    ]

    page._driver.locator("#faqAccordionItem2").click()
    faq_answer_elem = page._driver.locator("#faqAccordionItemExpand2")
    assert faq_answer_elem.inner_text() in [
        faq_answer_text.format(product=product) for product in products
    ]

    page.navigate_to(MainMenuPages.SOURCES)

    refresh_button = page._driver.locator(
        "button[data-ouia-component-id=refresh] span[class$=button__text]"
    )
    assert refresh_button.inner_text() == "Refreshed just now"

    page.logout()
