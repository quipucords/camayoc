# coding=utf-8
"""Utility class for UI tests."""
import time

import pytest

from selenium.common.exceptions import (
        NoSuchElementException,
        StaleElementReferenceException
)
from selenium.webdriver.remote.webelement import WebElement

from smartloc import Locator

from widgetastic.exceptions import WidgetOperationFailed
from widgetastic.widget import Checkbox, GenericLocatorWidget, TextInput

from widgetastic_patternfly import Button, Dropdown

from .views import (
        CredentialModalView,
        DashboardView,
        DeleteModalView,
        SourceModalView
    )


SOURCE_TYPE_RADIO_LABELS = {
    'Network': 'Network Range',
    'Satellite': 'Satellite',
    'VCenter': 'vCenter Server'
    }


def wait_for_animation(multiplier=1):
    """Wait for animations to complete."""
    time.sleep(0.5 * multiplier)


def row_xpath(row_name):
    """Build an xpath for selecting a certain row.

    Works for credentials or sources.
    """
    return (f'//div[contains(@class, "list-view-pf-top-align")'
            f' and descendant::div[text()="{row_name}"]]')


def checkbox_xpath(row_name):
    """Build an xpath for selecting a checkbox in a row.

    Works for credentials or sources.
    """
    return (f'//div[contains(@class, "list-view-pf-top-align")'
            f' and descendant::div[text()="{row_name}"]]'
            f'/descendant::input[contains(@type,"checkbox")]')


def delete_xpath(row_name):
    """Return an xpath for selecting the delete button in a row.

    Works for credentials or sources.
    """
    return (f'//div[contains(@class, "list-view-pf-top-align") and '
            f'descendant::div[text()="{row_name}"]]/descendant::span'
            f'[contains(@class, "pficon-delete")]')


def check_auth_type(credential_name, auth_type):
    """Verify the authentication type of a credential.

    Example types include 'SSH Key' and 'Username and Password'.
    If the Locator cannot find a match, an exception is raised.
    """
    Locator(xpath=(f'//span[text()="{auth_type}" and ancestor::node()[2]'
                   f'//*[text()="{credential_name}"]]'))


def set_checkbox(view, name, fill):
    """Fill or clear a checkbox next to a credential."""
    checkbox = Checkbox(view, locator=Locator(
        xpath=checkbox_xpath(name)))
    try:
        checkbox.fill(fill)
    except WidgetOperationFailed:
        clear_toasts(view=view)
        checkbox.fill(fill)


def fill(view, xpath_locator, text):
    """Fill in a textbox using a xpath locator."""
    TextInput(view, locator=Locator(xpath=xpath_locator)).fill(text)


def field_xpath(label, textarea=False):
    """Build an xpath for selecting a form field based on its label."""
    if textarea:
        return (f'//textarea[ancestor::node()[2]/label[text() = "{label}"]]')
    else:
        return (f'//input[ancestor::node()[2]/label[text() = "{label}"]]')


def radio_xpath(label):
    """Build an xpath for selecting a radio button based on its label."""
    return f'//label[text()="{label}"]'


def clear_toasts(view, count=20):
    """Attempt to flush any confirmation dialogs that may have appeared.

    Use this function to clear out dialogs (toasts) that may be
    preventing buttons from being clicked properly. Sometimes it might
    need to be used in succession. By default, this tries to flush a maximum
    of 20 toasts, but will quit early if it cannot find more.
    """
    for i in range(count):
        try:
            view.wait_for_element(locator=Locator(css='.close'), timeout=0.6)
            GenericLocatorWidget(view, locator=Locator(css='.close')).click()
        except (NoSuchElementException, StaleElementReferenceException):
            break


def create_credential(view, options):
    """Create a credential through the UI."""
    clear_toasts(view=view)
    dash = DashboardView(view)
    dash.nav.select('Credentials')
    # Display differs depending on whether or not credentials already exist.
    try:
        add_credential_dropdown = Dropdown(view, 'Add Credential')
        add_credential_dropdown.item_select(
                options['credential_type'] + ' Credential')
    except NoSuchElementException:
        add_credential_dropdown = Dropdown(view, 'Add')
        add_credential_dropdown.item_select(
                options['credential_type'] + ' Credential')
    modal = CredentialModalView(view, locator=Locator(css='.modal-content'))

    # Workaround, should be `assert modal.save_button.disabled`
    # https://github.com/RedHatQE/widgetastic.patternfly/pull/66
    # https://github.com/quipucords/camayoc/issues/279
    assert modal.save_button.browser.get_attribute(
        'disabled', modal.save_button)

    # Fill in the required credential information.
    fill(modal, field_xpath('Credential Name'), options['name'])
    fill(modal, field_xpath('Username'), options['username'])
    if 'sshkeyfile' in options:
        auth_type = Dropdown(view, 'Username and Password')
        auth_type.item_select('SSH Key')
        fill(modal, field_xpath('SSH Key File'), options['sshkeyfile'])
        fill(modal, field_xpath('Passphrase'), options['passphrase'])
    else:
        fill(modal, field_xpath('Password'), options['password'])
    if 'become_user' in options:
        fill(modal, field_xpath('Become User'), options['become_user'])
        fill(modal, field_xpath('Become Password'), options['become_pass'])

    assert not modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)

    # Hack to deal with the fact that the GET refresh isn't
    # implemented when the save button is clicked.
    # https://github.com/quipucords/quipucords/issues/1399
    # https://github.com/quipucords/camayoc/issues/280
    wait_for_animation()
    modal.save_button.click()
    wait_for_animation()
    view.refresh()
    dash.nav.select('Credentials')
    # Assert the row with the credential name exists.
    view.wait_for_element(locator=Locator(
        xpath=row_xpath(options['name'])), delay=0.3)
    assert isinstance(view.element(locator=Locator(
        xpath=row_xpath(options['name']))), WebElement)


def delete_credential(view, names):
    """Delete a credential through the UI."""
    view.refresh()
    dash = DashboardView(view)
    dash.nav.select('Credentials')
    # Select all the checkboxes next to the credentials to be deleted.
    for name in names:
        set_checkbox(view, name, True)
    Button(view, 'Delete').click()
    DeleteModalView(view, locator=Locator(
        css='.modal-content')).delete_button.click()
    # Wait for the deletion animations to complete,
    # and verify that the rows are gone.
    wait_for_animation(2)
    for name in names:
        with pytest.raises(NoSuchElementException):
            view.wait_for_element(locator=Locator(
                xpath=row_xpath(name)), timeout=1)


def create_source(view, credential_name, source_type, source_name, addresses):
    """Create a source through the UI."""
    clear_toasts(view=view)
    dash = DashboardView(view)
    dash.nav.select('Sources')
    # Display varies depending on whether or not sources already exist.
    try:
        Button(view, 'Add Source').click()
    except NoSuchElementException:
        Button(view, 'Add').click()

    # Source creation wizard
    modal = SourceModalView(view, locator=Locator(css='.modal-content'))
    radio_label = SOURCE_TYPE_RADIO_LABELS[source_type]

    # Wait for radio button to become responsive before clicking a source type.
    wait_for_animation()
    GenericLocatorWidget(modal, locator=Locator(
        xpath=radio_xpath(radio_label))).click()
    modal.next_button.click()

    # Fill in required source information.
    fill(modal, field_xpath('Name'), source_name)
    if source_type is 'Network':
        fill(modal, field_xpath('Search Addresses', textarea=True), addresses)
        fill(modal, field_xpath('Port'), '')  # default port of 22
        cred_dropdown = Dropdown(modal, 'Select one or more credentials')
        cred_dropdown.item_select(credential_name)
    else:
        fill(modal, field_xpath('IP Address or Hostname'), addresses)
        cred_dropdown = Dropdown(modal, 'Select a credential')
        cred_dropdown.item_select(credential_name)
    Button(modal, 'Save').click()
    view.wait_for_element(locator=Locator('//button[text()="Close"]'))
    Button(modal, 'Close', classes=[Button.PRIMARY]).click()

    # Verify that the new row source has been created.
    view.wait_for_element(locator=Locator(xpath=row_xpath(source_name)))
    view.element(locator=Locator(xpath=row_xpath(source_name)))


def delete_source(view, source_name):
    """Delete a source through the UI."""
    clear_toasts(view=view)
    dash = DashboardView(view)
    dash.nav.select('Sources')
    wait_for_animation()
    view.wait_for_element(locator=Locator(
        xpath=(delete_xpath(source_name))))
    GenericLocatorWidget(view, locator=Locator(
        xpath=delete_xpath(source_name))).click()
    wait_for_animation()
    DeleteModalView(view).delete_button.click()
    view.refresh()
    with pytest.raises(NoSuchElementException):
        view.wait_for_element(locator=Locator(xpath=delete_xpath(source_name)),
                              timeout=1)
