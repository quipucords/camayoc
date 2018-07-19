# coding=utf-8
"""Tests for handling sources in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from uuid import uuid4


from selenium.common.exceptions import NoSuchElementException


from smartloc import Locator


from widgetastic.widget import Checkbox


from widgetastic_patternfly import Button, Dropdown


from .utils import clear_toasts, fill
from .views import CredentialModalView, DashboardView, DeleteModalView


def create_credential(view):
    """Create a credential through the UI."""
    dash = DashboardView(view)
    dash.nav.select('Credentials')
    try:
        add_credential_dropdown = Dropdown(view, 'Add Credential')
        add_credential_dropdown.item_select('Network Credential')
    except NoSuchElementException:
        add_credential_dropdown = Dropdown(view, 'Add')
        add_credential_dropdown.item_select('Network Credential')
    modal = CredentialModalView(view, locator=Locator(css='.modal-content'))

    # workaround, should be `assert modal.save_button.disabled`
    # https://github.com/RedHatQE/widgetastic.patternfly/pull/66
    assert modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)
    fill(modal, '[placeholder="Enter a name for the credential"]', uuid4())
    fill(modal, '[placeholder="Enter Username"]', uuid4())
    fill(modal, '[placeholder="Enter Password"]', uuid4())
    assert not modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)
    modal.save_button.click()

    # clear any artifacts from confirmation dialog, use checkbox as a canary
    view.wait_for_element(
            locator=Locator(css='[type="checkbox"]'), delay=0.3)
    clear_toasts(view=view)


def test_create_delete_credential(browser, qpc_login):
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
    create_credential(browser)
    # Confirmation alert covers checkboxes and buttons when clicking
    check = Checkbox(browser, locator=Locator(css='[type="checkbox"]'))
    check.fill(True)
    Button(browser, 'Delete').click()
    DeleteModalView(browser, locator=Locator(
                        css='.modal-content')).delete_button.click()
