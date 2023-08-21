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

from camayoc.qpc_models import Source
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AddSourceDTOFactory
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import SourceTypes
from camayoc.ui.types import NetworkSourceFormDTO
from camayoc.ui.types import SatelliteSourceFormDTO
from camayoc.ui.types import SourceFormDTO
from camayoc.ui.types import VCenterSourceFormDTO

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
}


CREDENTIAL_TYPES_MAP = {
    NetworkSourceFormDTO: "network",
    SatelliteSourceFormDTO: "satellite",
    VCenterSourceFormDTO: "vcenter",
}


SOURCE_TYPES_MAP = {
    NetworkSourceFormDTO: SourceTypes.NETWORK_RANGE,
    SatelliteSourceFormDTO: SourceTypes.SATELLITE,
    VCenterSourceFormDTO: SourceTypes.VCENTER_SERVER,
}


def create_source_dto(source_type, data_provider):
    credential_type = CREDENTIAL_TYPES_MAP.get(source_type)
    credential_model = data_provider.credentials.new_one({"type": credential_type}, data_only=False)

    source_address = random.choice(SOURCE_DATA_MAP.get(source_type))
    extra_source_kwargs = {}
    if issubclass(source_type, NetworkSourceFormDTO):
        extra_source_kwargs["source_form__addresses"] = [source_address]
    else:
        extra_source_kwargs["source_form__address"] = source_address

    source_dto = AddSourceDTOFactory(
        select_source_type__source_type=SOURCE_TYPES_MAP.get(source_type),
        source_form__credentials=[credential_model.name],
        **extra_source_kwargs,
    )
    data_provider.mark_for_cleanup(Source(name=source_dto.source_form.source_name))
    return source_dto


# FIXME: this never actually deletes in UI
@pytest.mark.parametrize("source_type", get_args(SourceFormDTO))
def test_create_delete_source(data_provider, ui_client: Client, source_type):
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
    source_dto = create_source_dto(source_type, data_provider)
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .logout()
    )
