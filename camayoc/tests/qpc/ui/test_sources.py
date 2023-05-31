# coding=utf-8
"""Test for handling sources in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
:upstream: yes
"""
import pytest

from camayoc.qpc_models import Credential
from camayoc.qpc_models import Source
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AddCredentialDTOFactory
from camayoc.ui.data_factories import AddSourceDTOFactory
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages
from camayoc.ui.enums import SourceTypes

SOURCE_DATA = {
    SourceTypes.NETWORK_RANGE: [
        "127.0.0.1",
        "127.0.0.1, 127.0.0.2",
        "192.168.1.[1:100]",
        "192.168.0.0/24",
        "example.sonar.com",
    ],
    SourceTypes.SATELLITE: ["127.0.0.1", "examplesatellite.sonar.com"],
    SourceTypes.VCENTER_SERVER: ["127.0.0.1", "examplevcenter.sonar.com"],
}

MATCHING_TYPES = {
    SourceTypes.NETWORK_RANGE: CredentialTypes.NETWORK,
    SourceTypes.SATELLITE: CredentialTypes.SATELLITE,
    SourceTypes.VCENTER_SERVER: CredentialTypes.VCENTER,
}


@pytest.mark.parametrize("source_type, ", SOURCE_DATA.keys())
def test_create_delete_source(ui_client: Client, source_type, cleanup):
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

    credential_type = MATCHING_TYPES[source_type]
    credential_data = AddCredentialDTOFactory(credential_type=credential_type)
    source_data = AddSourceDTOFactory(
        select_source_type__source_type=source_type,
        source_form__credentials=[credential_data.credential_form_dto.credential_name],
    )
    cleanup.append(Credential(name=credential_data.credential_form_dto.credential_name))
    cleanup.append(Source(name=source_data.source_form.source_name))
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_data)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_data)
        .logout()
    )
