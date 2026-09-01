# coding=utf-8
"""Tests for handling vault-backed credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import random

import pytest

from camayoc.qpc_models import Credential
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages

VAULT_AUTH_LABEL = "Vault secret path"

ALL_CREDENTIAL_FACTORIES = {
    CredentialTypes.OPENSHIFT: [
        data_factories.PlainOpenShiftCredentialFormDTOFactory,
        data_factories.TokenOpenShiftCredentialFormDTOFactory,
        data_factories.VaultOpenShiftCredentialFormDTOFactory,
    ],
    CredentialTypes.ANSIBLE: [
        data_factories.PlainAnsibleCredentialFormDTOFactory,
        data_factories.VaultAnsibleCredentialFormDTOFactory,
    ],
}


@pytest.mark.parametrize(
    "credential_type",
    [CredentialTypes.OPENSHIFT, CredentialTypes.ANSIBLE],
    ids=["openshift", "ansible"],
)
def test_vault_option_disabled_when_not_configured(
    unconfigured_vault_server, ui_client: Client, credential_type
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
    page = (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .open_add_credential(credential_type)
    )

    auth_dropdown = page._driver.locator("button[data-ouia-component-id=auth_type]")
    auth_dropdown.click()

    vault_option = page._driver.locator(f"[role='menuitem']:has-text('{VAULT_AUTH_LABEL}')")
    assert vault_option.is_visible(), f"Vault option '{VAULT_AUTH_LABEL}' should be visible"
    assert vault_option.get_attribute("aria-disabled") == "true", (
        f"Vault option '{VAULT_AUTH_LABEL}' should be disabled when vault is not configured"
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
    "credential_type",
    [CredentialTypes.OPENSHIFT, CredentialTypes.ANSIBLE],
    ids=["openshift", "ansible"],
)
def test_edit_vault_credential(
    configured_vault_server,
    data_provider,
    ui_client: Client,
    credential_type,
):
    """Create and then edit a credential in the quipucords UI.

    :id: b9c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e
    :description: Creates a credential (vault or non-vault), then edits it to
        use a randomly selected authentication type. Over many runs this covers
        vault->non-vault, non-vault->vault, and vault->vault transitions.
    :steps:
        1) Go to the credentials page and create a credential.
        2) Open the modal for editing the created credential.
        3) Modify the credential to use a different auth type and save changes.
    :expectedresults: The credential is created and then successfully edited.
    """
    factories = ALL_CREDENTIAL_FACTORIES[credential_type]

    initial_factory = random.choice(factories)
    credential_form = initial_factory()
    credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=credential_type,
        credential_form=credential_form,
    )
    data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))

    modified_factory = random.choice(factories)
    modified_form = modified_factory()
    edit_credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=credential_type,
        credential_form=modified_form,
    )
    # The edit renames the credential, so its post-edit name must also be
    # marked for cleanup to avoid leaking it on the server.
    data_provider.mark_for_cleanup(Credential(name=modified_form.credential_name))

    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .edit_credential(credential_form.credential_name, edit_credential_dto)
        .logout()
    )
