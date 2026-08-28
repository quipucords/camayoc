# coding=utf-8
"""Tests for handling vault-backed credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import pytest

from camayoc.qpc_models import Credential
from camayoc.tests.qpc.cli.utils import clear_server_vault
from camayoc.tests.qpc.cli.utils import configure_server_vault
from camayoc.tests.qpc.cli.utils import setup_qpc
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages


@pytest.fixture
def configured_vault_server():
    """Configure Discovery server vault settings for the test, then clear them."""
    setup_qpc()  # Configure and login qpc CLI
    clear_server_vault()
    configure_server_vault()
    yield
    clear_server_vault()


@pytest.mark.parametrize(
    "credential_type,auth_type_label",
    [
        (CredentialTypes.OPENSHIFT, "Vault secret path"),
        (CredentialTypes.ANSIBLE, "Vault secret path"),
    ],
    ids=["openshift", "ansible"],
)
def test_vault_option_disabled_when_not_configured(
    ui_client: Client, credential_type, auth_type_label
):
    """Verify vault option is visible but disabled when vault is not configured.

    :id: d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a
    :description: When HashiCorp Vault is not configured on the server, the
        "Vault secret path" authentication option should be visible in the
        dropdown but disabled (not selectable).
    :steps:
        1) Ensure vault is NOT configured on the server (clear any config)
        2) Log into the UI
        3) Go to Credentials page and open Add Credential modal
        4) Select credential type (OpenShift or Ansible)
        5) Open the authentication type dropdown
        6) Verify "Vault secret path" option is present but disabled
    :expectedresults: The "Vault secret path" option appears in the dropdown
        but has aria-disabled="true" attribute, preventing selection.
    """
    # Ensure vault is cleared (initialize CLI first to avoid order-dependency)
    setup_qpc()
    clear_server_vault()

    # Navigate to credentials and open the form
    page = (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .open_add_credential(credential_type)
    )

    # Open authentication type dropdown
    auth_dropdown = page._driver.locator("button[data-ouia-component-id=auth_type]")
    auth_dropdown.click()

    # Check that vault option exists but is disabled
    # PatternFly DropdownItem renders menu items with role="menuitem"
    vault_option = page._driver.locator(f"[role='menuitem']:has-text('{auth_type_label}')")
    assert vault_option.is_visible(), f"Vault option '{auth_type_label}' should be visible"
    assert vault_option.get_attribute("aria-disabled") == "true", (
        f"Vault option '{auth_type_label}' should be disabled when vault not configured"
    )

    page.cancel().logout()


@pytest.mark.parametrize(
    "credential_type,auth_type_label",
    [
        (CredentialTypes.OPENSHIFT, "Vault secret path"),
        (CredentialTypes.ANSIBLE, "Vault secret path"),
    ],
    ids=["openshift", "ansible"],
)
def test_vault_option_enabled_when_configured(
    configured_vault_server, ui_client: Client, credential_type, auth_type_label
):
    """Verify vault option is enabled when vault is configured.

    :id: e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b
    :description: When HashiCorp Vault is properly configured on the server
        (returning 200), the "Vault secret path" authentication option should
        be enabled and selectable.
    :steps:
        1) Configure HashiCorp Vault settings on the server
        2) Log into the UI
        3) Go to Credentials page and open Add Credential modal
        4) Select credential type (OpenShift or Ansible)
        5) Open the authentication type dropdown
        6) Verify "Vault secret path" option is enabled and can be selected
    :expectedresults: The "Vault secret path" option appears in the dropdown
        and does NOT have aria-disabled="true", allowing selection. When
        selected, vault-specific fields appear in the form.
    """
    # Navigate to credentials and open the form
    page = (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .open_add_credential(credential_type)
    )

    # Open authentication type dropdown
    auth_dropdown = page._driver.locator("button[data-ouia-component-id=auth_type]")
    auth_dropdown.click()

    # Check that vault option exists and is enabled
    # PatternFly DropdownItem renders menu items with role="menuitem"
    vault_option = page._driver.locator(f"[role='menuitem']:has-text('{auth_type_label}')")
    assert vault_option.is_visible(), f"Vault option '{auth_type_label}' should be visible"
    aria_disabled = vault_option.get_attribute("aria-disabled")
    assert aria_disabled != "true", (
        f"Vault option '{auth_type_label}' should be enabled when vault is configured"
    )

    # Select vault option to verify it's functional
    vault_option.click()

    # Verify vault-specific fields appear
    vault_secret_path_field = page._driver.locator(
        "input[data-ouia-component-id=vault_secret_path]"
    )
    vault_secret_key_field = page._driver.locator("input[data-ouia-component-id=vault_secret_key]")
    assert vault_secret_path_field.is_visible(), (
        "Vault secret path field should be visible when vault auth is selected"
    )
    assert vault_secret_key_field.is_visible(), (
        "Vault secret key field should be visible when vault auth is selected"
    )

    page.cancel().logout()


@pytest.mark.parametrize(
    "credential_factory,credential_type",
    [
        (
            data_factories.VaultOpenShiftCredentialFormDTOFactory,
            CredentialTypes.OPENSHIFT,
        ),
        (
            data_factories.VaultAnsibleCredentialFormDTOFactory,
            CredentialTypes.ANSIBLE,
        ),
    ],
    ids=["openshift-vault", "ansible-vault"],
)
def test_create_vault_credential(
    configured_vault_server,
    data_provider,
    ui_client: Client,
    credential_factory,
    credential_type,
):
    """Create a vault-backed credential in the quipucords UI.

    :id: a8b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
    :description: Go to the credentials page and create a vault-backed credential
        for OpenShift or Ansible sources.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Select the credential type (OpenShift or Ansible).
        4) Select "Vault secret path" from the authentication type dropdown.
        5) Fill in the vault credential fields (vault_secret_path, vault_secret_key,
           optional vault_mount_point) and save.
    :expectedresults: A new vault-backed credential is created successfully.
        The authentication type is set to "Vault secret path" and the vault
        fields are populated correctly.
    """
    credential_form = credential_factory()
    credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=credential_type,
        credential_form=credential_form,
    )
    data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))

    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .logout()
    )


@pytest.mark.parametrize(
    "credential_factory,credential_type",
    [
        (
            data_factories.VaultOpenShiftCredentialFormDTOFactory,
            CredentialTypes.OPENSHIFT,
        ),
        (
            data_factories.VaultAnsibleCredentialFormDTOFactory,
            CredentialTypes.ANSIBLE,
        ),
    ],
    ids=["openshift-vault", "ansible-vault"],
)
def test_edit_vault_credential(
    configured_vault_server,
    data_provider,
    ui_client: Client,
    credential_factory,
    credential_type,
):
    """Create and then edit a vault-backed credential in the quipucords UI.

    :id: b9c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e
    :description: Creates a vault-backed credential and then edits it in the UI.
    :steps:
        1) Go to the credentials page and create a vault-backed credential.
        2) Open the modal for editing the created credential.
        3) Modify some of the vault credential information and save changes.
    :expectedresults: The vault-backed credential is created and then
        successfully edited.
    """
    # Create initial vault credential
    credential_form = credential_factory()
    credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=credential_type,
        credential_form=credential_form,
    )
    data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))

    # Create modified version for editing - keep the same credential name for cleanup
    modified_form = credential_factory(credential_name=credential_form.credential_name)
    edit_credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=credential_type,
        credential_form=modified_form,
    )

    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .edit_credential(credential_form.credential_name, edit_credential_dto)
        .logout()
    )
