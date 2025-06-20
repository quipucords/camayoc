# coding=utf-8
"""Test for handling sources in the UI.

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

from camayoc.exceptions import NoMatchingDataDefinitionException
from camayoc.qpc_models import Source
from camayoc.types.ui import AddSourceDTO
from camayoc.types.ui import AnsibleSourceFormDTO
from camayoc.types.ui import NetworkSourceFormDTO
from camayoc.types.ui import OpenShiftSourceFormDTO
from camayoc.types.ui import RHACSSourceFormDTO
from camayoc.types.ui import SatelliteSourceFormDTO
from camayoc.types.ui import SourceFormDTO
from camayoc.types.ui import VCenterSourceFormDTO
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AddSourceDTOFactory
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import SourceConnectionTypes
from camayoc.ui.enums import SourceTypes

SOURCE_DATA_MAP = {
    NetworkSourceFormDTO: [
        "127.0.0.1",
        "127.0.0.1, 127.0.0.2",
        "192.168.1.[1:100]",
        "192.168.0.0/24",
        "example.sonar.com",
    ],
    SatelliteSourceFormDTO: ["127.0.0.1", "examplesatellite.sonar.com"],
    VCenterSourceFormDTO: ["127.0.0.1", "examplevcenter.sonar.com"],
    OpenShiftSourceFormDTO: ["127.0.0.1", "exampleopenshift.sonar.com"],
    AnsibleSourceFormDTO: ["127.0.0.1", "exampleansible.sonar.com"],
    RHACSSourceFormDTO: ["127.0.0.1", "acs.exampleopenshift.sonar.com"],
}


CREDENTIAL_DP_TYPES_MAP = {
    NetworkSourceFormDTO: "network",
    SatelliteSourceFormDTO: "satellite",
    VCenterSourceFormDTO: "vcenter",
    OpenShiftSourceFormDTO: "openshift",
    AnsibleSourceFormDTO: "ansible",
    RHACSSourceFormDTO: "rhacs",
}


CREDENTIAL_DTO_TYPES_MAP = {
    NetworkSourceFormDTO: CredentialTypes.NETWORK,
    SatelliteSourceFormDTO: CredentialTypes.SATELLITE,
    VCenterSourceFormDTO: CredentialTypes.VCENTER,
    OpenShiftSourceFormDTO: CredentialTypes.OPENSHIFT,
    AnsibleSourceFormDTO: CredentialTypes.ANSIBLE,
    RHACSSourceFormDTO: CredentialTypes.RHACS,
}


SOURCE_TYPES_MAP = {
    NetworkSourceFormDTO: SourceTypes.NETWORK_RANGE,
    SatelliteSourceFormDTO: SourceTypes.SATELLITE,
    VCenterSourceFormDTO: SourceTypes.VCENTER_SERVER,
    OpenShiftSourceFormDTO: SourceTypes.OPENSHIFT,
    AnsibleSourceFormDTO: SourceTypes.ANSIBLE_CONTROLLER,
    RHACSSourceFormDTO: SourceTypes.RHACS,
}


def create_source_dto(source_type, data_provider):
    credential_dp_type = CREDENTIAL_DP_TYPES_MAP.get(source_type)
    try:
        credential_model = data_provider.credentials.new_one(
            {"type": credential_dp_type}, data_only=False
        )
    except NoMatchingDataDefinitionException:
        credential_dto = data_factories.AddCredentialDTOFactory(
            credential_type=CREDENTIAL_DTO_TYPES_MAP.get(source_type)
        )
        credential_model = credential_dto.credential_form.to_model()
        credential_model.create()
        data_provider.mark_for_cleanup(credential_model)

    source_address = random.choice(SOURCE_DATA_MAP.get(source_type))
    extra_source_kwargs = {}
    if issubclass(source_type, NetworkSourceFormDTO):
        extra_source_kwargs["source_form__addresses"] = [source_address]
    else:
        extra_source_kwargs["source_form__address"] = source_address

    source_dto = AddSourceDTOFactory(
        source_type=SOURCE_TYPES_MAP.get(source_type),
        source_form__credentials=[credential_model.name],
        **extra_source_kwargs,
    )
    data_provider.mark_for_cleanup(Source(name=source_dto.source_form.source_name))
    return source_dto


def modify_source_dto(source_dto: AddSourceDTO, data_provider):
    source_form_cls = source_dto.source_form.__class__
    another_source = create_source_dto(source_form_cls, data_provider)
    dto_fields = fields_dict(source_form_cls).keys()
    updated_fields = random.sample(list(dto_fields), k=random.randint(1, len(dto_fields)))
    updated_fields = {key: getattr(another_source.source_form, key) for key in updated_fields}
    new_form_dto = evolve(source_dto.source_form, **updated_fields)
    if getattr(new_form_dto, "connection", None) == SourceConnectionTypes.DISABLE:
        new_form_dto = evolve(new_form_dto, verify_ssl=None)
    new_dto = evolve(source_dto, source_form=new_form_dto)
    return new_dto


# FIXME: this never actually deletes in UI
@pytest.mark.parametrize("source_type", get_args(SourceFormDTO))
def test_create_delete_source(cleaning_data_provider, ui_client: Client, source_type):
    """Create and then delete a source through the UI.

    :id: b1f64fd6-0421-4650-aa6d-149cb3099012
    :description: Creates a source in the UI.
    :steps:
        1) Go to the sources page and open the sources modal.
        2) Fill in the required information and create a new source.
        3) Remove the newly created source.
    :expectedresults: A new source is created with the provided information,
        then it is deleted.
    """
    source_dto = create_source_dto(source_type, cleaning_data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .logout()
    )


@pytest.mark.parametrize("source_type", get_args(SourceFormDTO))
def test_edit_source(cleaning_data_provider, ui_client: Client, source_type):
    """Create and then a edit a source through the UI.

    :id: 8c3e75fe-40d7-44c6-846a-29a724db0ea2
    :description: Creates and edits a source in the UI.
    :steps:
        1) Go to the sources page and open the sources modal.
        2) Fill in the required information and create a new source.
        3) Open the modal for editing of created source.
        4) Modify some of the information and save changes.
    :expectedresults: A new source is created with the provided information,
        then it is modified.
    """
    source_dto = create_source_dto(source_type, cleaning_data_provider)
    edit_source_dto = modify_source_dto(source_dto, cleaning_data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .edit_source(source_dto.source_form.source_name, edit_source_dto)
        .logout()
    )
