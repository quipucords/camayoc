# coding=utf-8
"""Tests for handling credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import random
from typing import get_args

import pytest
from attrs import evolve
from attrs import fields_dict
from littletable import Table

from camayoc.config import settings
from camayoc.qpc_models import Credential
from camayoc.types.ui import AddCredentialDTO
from camayoc.types.ui import AnsibleCredentialFormDTO
from camayoc.types.ui import CredentialFormDTO
from camayoc.types.ui import NetworkCredentialFormDTO
from camayoc.types.ui import OpenShiftCredentialFormDTO
from camayoc.types.ui import PlainNetworkCredentialFormDTO
from camayoc.types.ui import RHACSCredentialFormDTO
from camayoc.types.ui import SatelliteCredentialFormDTO
from camayoc.types.ui import SSHNetworkCredentialFormDTO
from camayoc.types.ui import VaultAnsibleCredentialFormDTO
from camayoc.types.ui import VaultOpenShiftCredentialFormDTO
from camayoc.types.ui import VCenterCredentialFormDTO
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages

CREDENTIAL_TYPE_MAP = {
    SatelliteCredentialFormDTO: CredentialTypes.SATELLITE,
    VCenterCredentialFormDTO: CredentialTypes.VCENTER,
    RHACSCredentialFormDTO: CredentialTypes.RHACS,
}

VAULT_CREDENTIAL_FORM_DTOS = (
    VaultOpenShiftCredentialFormDTO,
    VaultAnsibleCredentialFormDTO,
)

VAULT_AUTH_LABEL = "Vault secret path"


def skip_if_vault_unavailable(credential_type):
    """Skip the test when it needs a vault that Camayoc does not know about."""
    if credential_type in VAULT_CREDENTIAL_FORM_DTOS and settings.hashicorp_vault is None:
        pytest.skip("hashicorp_vault is not defined in Camayoc configuration")


def available_credential_form_classes(credential_form_classes):
    """Drop vault-backed classes when Camayoc has no vault configuration."""
    if settings.hashicorp_vault is not None:
        return credential_form_classes
    return tuple(cls for cls in credential_form_classes if cls not in VAULT_CREDENTIAL_FORM_DTOS)


def create_credential_dto(credential_type, data_provider):
    if issubclass(credential_type, get_args(NetworkCredentialFormDTO)):
        factory_kwargs = {}
        form_factory_cls = getattr(data_factories, f"{credential_type.__name__}Factory")
        if issubclass(credential_type, PlainNetworkCredentialFormDTO):
            form_factory_cls = data_factories.PlainNetworkCredentialFormDTOFactory
        if issubclass(credential_type, SSHNetworkCredentialFormDTO):
            form_factory_cls = data_factories.SSHNetworkCredentialFormDTOFactory
            ssh_network_credential = data_provider.credentials.new_one(
                {"type": "network", "sshkeyfile": Table.is_not_null()},
                data_only=True,
            )
            factory_kwargs["ssh_key_file"] = ssh_network_credential.ssh_key
        credential_form = form_factory_cls(**factory_kwargs)
        credential = data_factories.AddCredentialDTOFactory(
            credential_type=CredentialTypes.NETWORK,
            credential_form=credential_form,
        )
        data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))
        return credential
    elif issubclass(credential_type, get_args(OpenShiftCredentialFormDTO)):
        form_factory_cls = getattr(data_factories, f"{credential_type.__name__}Factory")
        credential_form = form_factory_cls()
        credential = data_factories.AddCredentialDTOFactory(
            credential_type=CredentialTypes.OPENSHIFT, credential_form=credential_form
        )
        data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))
        return credential
    elif issubclass(credential_type, get_args(AnsibleCredentialFormDTO)):
        form_factory_cls = getattr(data_factories, f"{credential_type.__name__}Factory")
        credential_form = form_factory_cls()
        credential = data_factories.AddCredentialDTOFactory(
            credential_type=CredentialTypes.ANSIBLE, credential_form=credential_form
        )
        data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))
        return credential

    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CREDENTIAL_TYPE_MAP.get(credential_type)
    )
    data_provider.mark_for_cleanup(Credential(name=credential.credential_form.credential_name))
    return credential


def modify_credential_dto(credential_dto: AddCredentialDTO, data_provider):
    credential_form_cls = credential_dto.credential_form.__class__
    old_credential_form_cls = credential_form_cls
    network_classes = get_args(NetworkCredentialFormDTO)
    openshift_classes = get_args(OpenShiftCredentialFormDTO)
    ansible_classes = get_args(AnsibleCredentialFormDTO)

    # Authentication type is picked at random, so over enough runs the edit
    # covers every transition - including non-vault to vault and back.
    if issubclass(credential_form_cls, network_classes):
        credential_form_cls = random.choice(available_credential_form_classes(network_classes))
    elif issubclass(credential_form_cls, openshift_classes):
        credential_form_cls = random.choice(available_credential_form_classes(openshift_classes))
    elif issubclass(credential_form_cls, ansible_classes):
        credential_form_cls = random.choice(available_credential_form_classes(ansible_classes))

    another_credential = create_credential_dto(credential_form_cls, data_provider)

    if old_credential_form_cls == credential_form_cls:
        dto_fields = fields_dict(credential_form_cls).keys()
        updated_fields = random.sample(list(dto_fields), k=random.randint(1, len(dto_fields)))
        updated_fields = {
            key: getattr(another_credential.credential_form, key) for key in updated_fields
        }
        new_form_dto = evolve(credential_dto.credential_form, **updated_fields)
    else:
        new_form_dto = another_credential.credential_form
    new_dto = evolve(credential_dto, credential_form=new_form_dto)

    return new_dto


# FIXME: this never actually deletes in UI (deletion not implemented in page objects)
@pytest.mark.parametrize("credential_type", get_args(CredentialFormDTO))
def test_create_credential(
    optional_vault_server, data_provider, ui_client: Client, credential_type
):
    """Create a credential in the quipucords UI.

    :id: d9fd61f5-1e8e-4091-b8c5-bc787884c6be
    :description: Go to the credentials page and follow the creation process.
        Vault-backed authentication types are included, and are skipped when
        Camayoc configuration does not define a vault.
    :steps:
        1) Log into the UI.
        2) Go to the credentials page and open the Add Credential modal.
        3) Fill in required fields and save.
    :expectedresults: A new credential is created with the provided information.
    """
    skip_if_vault_unavailable(credential_type)

    credential_dto = create_credential_dto(credential_type, data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .logout()
    )


@pytest.mark.parametrize("credential_type", get_args(CredentialFormDTO))
def test_edit_credential(optional_vault_server, data_provider, ui_client: Client, credential_type):
    """Create and then edit a credential in the quipucords UI.

    :id: 3a4626ab-c667-41dc-944e-62ac05d51bbe
    :description: Creates and edits a credential in the UI. The authentication
        type used by the edit is picked at random, so over enough runs this
        covers non-vault to non-vault, non-vault to vault, vault to non-vault
        and vault to vault transitions.
    :steps:
        1) Go to the credentials page and open the credential modal.
        2) Fill in the required information and create a new credential.
        3) Open the modal for editing of created credential.
        4) Modify some of the information and save changes.
    :expectedresults: A new credential is created and then edited.
    """
    skip_if_vault_unavailable(credential_type)

    credential_dto = create_credential_dto(credential_type, data_provider)
    edit_credential_dto = modify_credential_dto(credential_dto, data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .edit_credential(credential_dto.credential_form.credential_name, edit_credential_dto)
        .logout()
    )


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
