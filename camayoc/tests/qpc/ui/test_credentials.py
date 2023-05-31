# coding=utf-8
"""Tests for handling credentials in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
:upstream: yes
"""
import random

import pytest

from camayoc.qpc_models import Credential
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import NetworkCredentialBecomeMethods


def credentials_provider():
    credential_form = data_factories.SSHNetworkCredentialFormDTOFactory(
        username="user",
        ssh_key_file="/sshkeys/id_rsa",
        passphrase="123456",
        become_method=NetworkCredentialBecomeMethods.SUDO,
        become_user="root",
        become_password="power!",
    )
    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=credential_form,
    )
    yield pytest.param(credential, id="network-ssh")
    credential_form = data_factories.PlainNetworkCredentialFormDTOFactory(
        username="cloud-user",
        password="123456",
        become_method=NetworkCredentialBecomeMethods.SUDO,
        become_user="root",
        become_password="power!",
    )
    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=credential_form,
    )
    yield pytest.param(credential, id="network-plain")
    credential = data_factories.AddCredentialDTOFactory(credential_type=CredentialTypes.SATELLITE)
    yield pytest.param(credential, id="satellite")
    credential = data_factories.AddCredentialDTOFactory(credential_type=CredentialTypes.VCENTER)
    yield pytest.param(credential, id="vcenter")


def network_credentials_provider():
    credential_form = data_factories.SSHNetworkCredentialFormDTOFactory(
        username="cloud-user",
        ssh_key_file="/sshkeys/id_rsa",
        passphrase="123456",
        become_method=random.choice(tuple(NetworkCredentialBecomeMethods)),
        become_user="superuser",
        become_password="12345678",
    )
    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=credential_form,
    )
    yield pytest.param(credential, id="network-ssh")
    credential_form = data_factories.PlainNetworkCredentialFormDTOFactory(
        username="cloud-user",
        password="123456",
        become_method=random.choice(tuple(NetworkCredentialBecomeMethods)),
        become_user="superuser",
        become_password="12345678",
    )
    credential = data_factories.AddCredentialDTOFactory(
        credential_type=CredentialTypes.NETWORK,
        credential_form_dto=credential_form,
    )
    yield pytest.param(credential, id="network-plain")


@pytest.mark.parametrize("credential", credentials_provider())
def test_create_delete_credential(ui_client: Client, credential, cleanup):
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
    cleanup.append(Credential(name=credential.credential_form_dto.credential_name))
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential)
        .logout()
    )


@pytest.mark.parametrize("credential", network_credentials_provider())
def test_create_delete_credential_optional(ui_client: Client, credential, cleanup):
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
    cleanup.append(Credential(name=credential.credential_form_dto.credential_name))
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential)
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
