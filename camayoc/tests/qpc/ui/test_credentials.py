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


from smartloc import Locator


from widgetastic.widget import Checkbox, GenericLocatorWidget as Widget


from widgetastic_patternfly import Button, Dropdown


from .utils import fill
from .views import CredentialModalView, DashboardView, DeleteModalView


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
    dash = DashboardView(browser)

    # TODO: The "Add Credential" button changes depending on whether or
    # not the list is empty. Add a backup that checks for both positions.
    # Currently, it assumes the list is empty.
    dash.nav.select('Credentials')
    add_credential_dropdown = Dropdown(browser, 'Add Credential')
    add_credential_dropdown.item_select('Network Credential')
    modal = CredentialModalView(browser, locator=Locator(css='.modal-content'))

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

    # TODO: make wait + action a single function.
    # Wait for the modal animation to close, then delete the new credential
    browser.wait_for_element(
            locator=Locator(css='[type="checkbox"]'), delay=0.3)
    check = Checkbox(browser, locator=Locator(css='[type="checkbox"]'))
    check.fill(True)

    # Confirmation alert covers the delete button and needs to be closed.
    browser.wait_for_element(locator=Locator(css='.close'))
    Widget(browser, locator=Locator(css='.close')).click()
    Button(browser, 'Delete').click()
    DeleteModalView(browser, locator=Locator(
                        css='.modal-content')).delete_button.click()
