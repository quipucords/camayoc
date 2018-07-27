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
import time

from selenium.common.exceptions import NoSuchElementException

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget

from widgetastic_patternfly import Button, Dropdown

from camayoc import utils

from .utils import (
        clear_toasts,
        field_xpath,
        fill,
        radio_xpath
)
from .views import DashboardView, DeleteModalView, SourceModalView


def test_create_source(browser, qpc_login, credentials):
    """Create a source through the UI.

    :id: b1f64fd6-0421-4650-aa6d-149cb3099012
    :description: Creates a source in the UI.
    :steps:
        1) Go to the sources page and open the sources modal.
        2) Fill in the required information and create a new source.
    :expectedresults: A new source is created with the provided information.
    """
    # TODO: Turn creation and deletion of sources into utility functions.
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
    cred_dropdown = Dropdown(modal, 'Select one or more credentials')
    cred_dropdown.item_select(credentials['Network'])
    Button(modal, 'Save').click()
    browser.wait_for_element(locator=Locator('//button[text()="Close"]'))
    Button(modal, 'Close', classes=[Button.PRIMARY]).click()
    time.sleep(0.3)  # wait for window animation to complete
    #  Deletion inherently asserts that the new sources exists in the UI.
    GenericLocatorWidget(browser, locator=Locator(
        xpath='//div[//*/text()="' + name +
        '"]//*[contains(@class, "pficon-delete")]')).click()
    DeleteModalView(browser).delete_button.click()
    clear_toasts(browser)
