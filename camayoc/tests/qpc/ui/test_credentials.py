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
import time
from pathlib import Path

import pytest

from selenium.common.exceptions import \
        NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from smartloc import Locator

from widgetastic.exceptions import WidgetOperationFailed
from widgetastic.widget import Checkbox

from widgetastic_patternfly import Button, Dropdown

from camayoc import utils

from .utils import clear_toasts, field_xpath, fill
from .views import CredentialModalView, DashboardView, DeleteModalView

CREDENTIAL_TYPES = ['Network', 'Satellite', 'VCenter']


def checkbox_xpath(credential_name):
    """Build an xpath for selecting a checkbox next to a credential."""
    return '//div[text()="' + str(credential_name) + \
        '"]/ancestor::node()[8]//*[@type="checkbox"]'


def check_auth_type(credential_name, auth_type):
    """Verify the authentication type of a credential.

    Example types include 'SSH Key' and 'Username and Password'.
    If the Locator cannot find a match, an exception is raised.
    """
    Locator(xpath='//span[text() = "' +
            auth_type + '" and ancestor::node()[2]//*[text()="' +
            credential_name + '"]]')


def set_checkbox(view, name, fill):
    """Fill or clear a checkbox next to a credential."""
    checkbox = Checkbox(view, locator=Locator(
        xpath=checkbox_xpath(name)))
    try:
        checkbox.fill(fill)
    except WidgetOperationFailed:
        clear_toasts(view=view)
        checkbox.fill(fill)


def create_credential(view, options):
    """Create a credential through the UI."""
    dash = DashboardView(view)
    dash.nav.select('Credentials')
    # Display differs depending on whether or not credentials already exist
    try:
        add_credential_dropdown = Dropdown(view, 'Add Credential')
        add_credential_dropdown.item_select(
                options['credential_type'] + ' Credential')
    except NoSuchElementException:
        add_credential_dropdown = Dropdown(view, 'Add')
        add_credential_dropdown.item_select(
                options['credential_type'] + ' Credential')
    modal = CredentialModalView(view, locator=Locator(css='.modal-content'))

    # workaround, should be `assert modal.save_button.disabled`
    # https://github.com/RedHatQE/widgetastic.patternfly/pull/66
    assert modal.save_button.browser.get_attribute(
            'disabled', modal.save_button)
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
    modal.save_button.click()

    # clear any artifacts from confirmation dialog
    view.wait_for_element(
            locator=Locator(xpath=checkbox_xpath(options['name'])), delay=0.3)
    clear_toasts(view=view)
    # Checkbox next to name of credential is used to check for existence
    assert isinstance(view.element(locator=Locator(
        xpath=checkbox_xpath(options['name']))), WebElement)


def delete_credential(view, name):
    """Delete a credential through the UI."""
    clear_toasts(view=view)
    Button(view, 'Delete').click()
    DeleteModalView(view, locator=Locator(
                        css='.modal-content')).delete_button.click()
    time.sleep(0.1)  # Wait for animation to finish before checking deletion
    with pytest.raises(
            (NoSuchElementException, StaleElementReferenceException)):
        view.element(locator=Locator(xpath=checkbox_xpath(name)))


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
    name = utils.uuid4()
    username = utils.uuid4()
    password = utils.uuid4()
    create_credential(browser, {
        'name': name,
        'username': username,
        'password': password,
        'credential_type': credential_type
        })
    set_checkbox(browser, name, True)
    delete_credential(browser, name)


def test_create_delete_credential_optional(browser, qpc_login):
    """Create and then delete a credential with optional parameters.

    :id: 37632616-86e9-47d1-b1f6-78dd5dde0774
    :description: Optional parameters are included in this test,
        like Become User and Become Password. Afterwards, the new
        credential is deleted.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Fill in required and optional fields and save.
        4) Delete the newly created credential.
    :expectedresults: A new credential is created and then deleted.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    password = utils.uuid4()
    become_user = utils.uuid4()
    become_pass = utils.uuid4()
    create_credential(browser, {
        'name': name,
        'username': username,
        'password': password,
        'credential_type': 'Network',
        'become_user': become_user,
        'become_pass': become_pass
        })
    set_checkbox(browser, name, True)
    delete_credential(browser, name)


def test_create_delete_credential_sshkey(
        isolated_filesystem, browser, qpc_login):
    """Create and then delete a credential using an sshkey file.

    :id: 5ec5847c-6d41-4e4a-9f22-cc433eb11078
    :description: An SSH keyfile is created and used in this test
        to create a credential, which is deleted afterwards.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Fill in required fields, using the SSH key option and save.
        4) Delete the newly created credential.
    :expectedresults: A new credential is created and then deleted.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    passphrase = utils.uuid4()
    create_credential(browser, {
        'name': name,
        'username': username,
        'sshkeyfile': str(sshkeyfile.resolve()),
        'passphrase': passphrase,
        'credential_type': 'Network'
        })
    check_auth_type(name, 'SSH Key')
    set_checkbox(browser, name, True)
    delete_credential(browser, name)


def test_credential_sshkey_optional(
        isolated_filesystem, browser, qpc_login):
    """Create/delete a credential that uses an sshkey file and optional parameters.

    :id: a602ab9b-ee76-45fd-bbb2-f6f074c66819
    :description: All optional parameters and an SSH key are used to create a
        credential. Afterwards, the credential is deleted.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Fill required + optional fields, using the SSH key option and save.
        4) Delete the newly created credential.
    :expectedresults: A new credential is created and then deleted.
    """
    name = utils.uuid4()
    username = utils.uuid4()
    sshkeyfile = Path(utils.uuid4())
    sshkeyfile.touch()
    passphrase = utils.uuid4()
    become_user = utils.uuid4()
    become_pass = utils.uuid4()
    create_credential(browser, {
        'name': name,
        'username': username,
        'sshkeyfile': str(sshkeyfile.resolve()),
        'passphrase': passphrase,
        'credential_type': 'Network',
        'become_user': become_user,
        'become_pass': become_pass
        })
    check_auth_type(name, 'SSH Key')
    set_checkbox(browser, name, True)
    delete_credential(browser, name)
