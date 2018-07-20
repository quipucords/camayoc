# coding=utf-8
"""Tests for handling credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from uuid import uuid4

import pytest

from selenium.common.exceptions import \
        NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from smartloc import Locator

from widgetastic.exceptions import WidgetOperationFailed
from widgetastic.widget import Checkbox

from widgetastic_patternfly import Button, Dropdown

from .utils import clear_toasts, fill
from .views import CredentialModalView, DashboardView, DeleteModalView

CREDENTIAL_TYPES = ['Network', 'Satellite', 'VCenter']


def checkbox_xpath(credential_name):
    """Build an xpath for selecting a checkbox next to a credential."""
    return '//div[text()="' + str(credential_name) + \
        '"]/ancestor::node()[8]//*[@type="checkbox"]'


def form_field_xpath(label):
    """Build an xpath for selecting a form field based on its label."""
    return '//input[ancestor::node()[2]/label[text() = "' + label + '"]]'


def create_credential(view, credential_type, name, username, password):
    """Create a credential through the UI."""
    dash = DashboardView(view)
    dash.nav.select('Credentials')
    try:
        add_credential_dropdown = Dropdown(view, 'Add Credential')
        add_credential_dropdown.item_select(credential_type + ' Credential')
    except NoSuchElementException:
        add_credential_dropdown = Dropdown(view, 'Add')
        add_credential_dropdown.item_select(credential_type + ' Credential')
    modal = CredentialModalView(view, locator=Locator(css='.modal-content'))

    # workaround, should be `assert modal.save_button.disabled`
    # https://github.com/RedHatQE/widgetastic.patternfly/pull/66
    assert modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)
    fill(modal, form_field_xpath('Credential Name'), name)
    fill(modal, form_field_xpath('Username'), username)
    fill(modal, form_field_xpath('Password'), password)
    assert not modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)
    modal.save_button.click()

    # clear any artifacts from confirmation dialog
    view.wait_for_element(
            locator=Locator(xpath=checkbox_xpath(name)), delay=0.3)
    clear_toasts(view=view)
    # Checkbox next to name of credential is used to check for existence
    assert isinstance(view.element(locator=Locator(
        xpath=checkbox_xpath(name))), WebElement)


@pytest.mark.parametrize('credential_type', CREDENTIAL_TYPES)
def test_create_delete_credential(browser, qpc_login, credential_type):
    """Create and then delete a credential in the quipucords UI.

    :id: d9fd61f5-1e8e-4091-b8c5-bc787884c6be
    :description: Go to the credentials page and follow the creation process.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Fill in required fields and save.
        4) Delete the newly created credential.
    :expectedresults: A new credential is created and then deleted.
    """
    name = uuid4()
    username = uuid4()
    password = uuid4()
    create_credential(browser, credential_type, name, username, password)
    # Confirmation alert sometimes covers checkboxes and buttons when clicking
    checkbox = Checkbox(browser, locator=Locator(
        xpath=checkbox_xpath(name)))
    try:
        checkbox.fill(True)
    except WidgetOperationFailed:
        clear_toasts(view=browser)
        checkbox.fill(True)
    Button(browser, 'Delete').click()
    DeleteModalView(browser, locator=Locator(
                        css='.modal-content')).delete_button.click()
    # Checkbox next to name of credential is used to check for existence
    with pytest.raises(
            (NoSuchElementException, StaleElementReferenceException)):
        browser.element(locator=Locator(xpath=checkbox_xpath(name)))
