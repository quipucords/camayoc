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
import pytest

from selenium.common.exceptions import NoSuchElementException

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget

from widgetastic_patternfly import Button

from camayoc import utils

from .utils import field_xpath, fill, radio_xpath
from .views import DashboardView, SourceModalView


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
    fill(modal, field_xpath('Search Addresses'), '127.0.0.1')
    fill(modal, field_xpath('Port'), '')  # default port of 22
    #  Create a credential with the inner modal
