# coding=utf-8
"""Test for handling sources in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from selenium.common.exceptions import NoSuchElementException

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget

from widgetastic_patternfly import Button, Dropdown

from camayoc import utils

from .utils import clear_toasts, field_xpath, fill, radio_xpath
from .views import DashboardView, DeleteModalView, SourceModalView, View


def test_create_source(browser, qpc_login):
    """Create a source through the UI.

    :id: b1f64fd6-0421-4650-aa6d-149cb3099012
    :description: Creates a source in the UI.
    :steps: TODO
    :expectedresults: TODO
    """
    dash = DashboardView(browser)
    dash.nav.select('Sources')
    try:
        Button(browser, 'Add Source').click()
    except NoSuchElementException:
        Button(browser, 'Add').click()

    modal = SourceModalView(browser, locator=Locator(css='.modal-content'))
    GenericLocatorWidget(
            modal, locator=Locator(xpath=radio_xpath('Network Range'))).click()
    modal.next_button.click()
    name = utils.uuid4()
    fill(modal, field_xpath('Name'), name)
    fill(modal, field_xpath('Search Addresses', textarea=True), '127.0.0.1')
    fill(modal, field_xpath('Port'), '')  # default port of 22
    # Add a credential to be used with the source
    # TODO: Make this a fixture to be used across tests
    GenericLocatorWidget(modal, locator=Locator(
                xpath='//button[contains(@title,"Add a credential")]')).click()
    popup = View(modal, locator=Locator(
        xpath='//div[not(contains(@class,"wizard-pf"))]' +
              '/div[contains(@class,"modal-content")]'))
    name = utils.uuid4()
    username = utils.uuid4()
    password = utils.uuid4()
    fill(popup, field_xpath('Credential Name'), name)
    fill(popup, field_xpath('Username'), username)
    fill(popup, field_xpath('Password'), password)
    # We have to be more selective to choose the save button on the top modal
    GenericLocatorWidget(modal, locator=Locator(
        xpath='//div[not(contains(@class, "wizard-pf-footer"))]' +
              '/button[text()="Save"]')).click()
    clear_toasts(browser)
    cred_dropdown = Dropdown(modal, 'Select one or more credentials')
    cred_dropdown.item_select(name)
    Button(modal, 'Save').click()
    browser.wait_for_element(locator=Locator('//button[text()="Close"]'))
    Button(modal, 'Close', classes=[Button.PRIMARY]).click()
    # Click the delete icon
    GenericLocatorWidget(browser, locator=Locator(
        xpath='//span[contains(@class, "pficon-delete")]' +
        '/ancestor::node()[5]//*[text()="' + name + '"]')).click()
    DeleteModalView(browser).delete_button.click()
