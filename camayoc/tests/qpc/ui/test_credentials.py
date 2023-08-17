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
from littletable import Table

from camayoc.qpc_models import Credential
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import NetworkCredentialBecomeMethods
from camayoc.ui.types import CredentialFormDTO
from camayoc.ui.types import NetworkCredentialFormDTO
from camayoc.ui.types import PlainNetworkCredentialFormDTO
from camayoc.ui.types import SatelliteCredentialFormDTO
from camayoc.ui.types import SSHNetworkCredentialFormDTO
from camayoc.ui.types import VCenterCredentialFormDTO

CREDENTIAL_TYPE_MAP = {
    SatelliteCredentialFormDTO: CredentialTypes.SATELLITE,
    VCenterCredentialFormDTO: CredentialTypes.VCENTER,
}


def create_credential_dto(credential_type, data_provider):
    if issubclass(credential_type, get_args(NetworkCredentialFormDTO)):
        factory_kwargs = {
            "username": "user",
            "become_method": random.choice(tuple(NetworkCredentialBecomeMethods)),
            "become_user": "root",
            "become_password": "power!",
        }
        form_factory_cls = getattr(data_factories, f"{credential_type.__name__}Factory")
        if issubclass(credential_type, PlainNetworkCredentialFormDTO):
            form_factory_cls = data_factories.PlainNetworkCredentialFormDTOFactory
            factory_kwargs["password"] = "123456"
        if issubclass(credential_type, SSHNetworkCredentialFormDTO):
            form_factory_cls = data_factories.SSHNetworkCredentialFormDTOFactory
            ssh_network_credential = data_provider.credentials.new_one(
                {"type": "network", "sshkeyfile": Table.is_not_null()},
                data_only=True,
            )
            ssh_factory_kwargs = {
                "ssh_key_file": ssh_network_credential.ssh_keyfile,
                "passphrase": "123456",
            }
            factory_kwargs.update(ssh_factory_kwargs)
        credential_form = form_factory_cls(**factory_kwargs)
        credential = data_factories.AddCredentialDTOFactory(
            credential_type=CredentialTypes.NETWORK,
            credential_form_dto=credential_form,
        )
        data_provider.mark_for_cleanup(Credential(name=credential_form.credential_name))
        return credential

    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CREDENTIAL_TYPE_MAP.get(credential_type)
    )
    data_provider.mark_for_cleanup(Credential(name=credential.credential_form_dto.credential_name))
    return credential


# FIXME: this never actually deletes in UI
@pytest.mark.parametrize("credential_type", get_args(CredentialFormDTO))
def test_create_delete_credential(data_provider, ui_client: Client, credential_type):
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
    credential_dto = create_credential_dto(credential_type, data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .logout()
    )


# @pytest.mark.parametrize("source_type", SOURCE_TYPES)
# def test_edit_credential(ui_client: Client, source_type):
#     """Edit a credential's parameters.

#     :id: 3a4626ab-c667-41dc-944e-62ac05d51bbe
#     :description: Creates a credential, then attempts to edit all of the
#         parameters that were set, then verifies that they were changed.
#     :steps:
#         1) Log into the UI.
#         2) Go to the credentials page and open the Add Credential modal.
#         3) Fill required + optional fields, using the password option and save.
#         4) Edit the credential parameters and save, make sure it changed.
#     :expectedresults: A new credential is created and then edited.
#     """
#     # options = {
#     #     "name": utils.uuid4(),
#     #     "username": utils.uuid4(),
#     #     "password": utils.uuid4(),
#     #     "source_type": source_type,
#     # }
#     # if source_type == "Network":
#     #     options["become_user"] = utils.uuid4()
#     # create_credential(selenium_browser, options)
#     # new_options = {
#     #     "name": utils.uuid4(),
#     #     "username": utils.uuid4(),
#     #     "password": utils.uuid4(),
#     #     "source_type": source_type,
#     # }
#     # if source_type == "Network":
#     #     new_options["become_user"] = utils.uuid4()
#     # edit_credential(selenium_browser, options["name"], new_options)
#     # delete_credential(selenium_browser, {new_options["name"]})
#     pass
