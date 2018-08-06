# coding=utf-8
"""Test for handling sources in the UI.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
from flaky import flaky

import pytest

from camayoc import utils

from .utils import create_source, delete_source

SOURCE_DATA = {
    'Network': [
        '127.0.0.1',
        '127.0.0.1, 127.0.0.2',
        '192.168.1.[1:100]',
        '192.168.0.0/24',
        'example.sonar.com'],
    'Satellite': [
        '127.0.0.1',
        'examplesatellite.sonar.com'],
    'VCenter': [
        '127.0.0.1',
        'examplevcenter.sonar.com'],
    }


@flaky(max_runs=15)
@pytest.mark.parametrize('source_type, ', SOURCE_DATA.keys())
def test_create_delete_source(browser, qpc_login, credentials, source_type):
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
    #  A dict of source names with the address parameters as keys is created.
    source_names = {}
    #  Credentials have to be the same type as the source, so we use pre-made
    #  credentials that exist for each type.
    credential_name = credentials[source_type]
    for addresses in SOURCE_DATA[source_type]:
        source_name = utils.uuid4()
        source_names[addresses] = source_name
        create_source(browser, credential_name, source_type,
                      source_name, addresses)
    #  Deletion internally asserts all new sources exist in the UI.
    for addresses in SOURCE_DATA[source_type]:
        delete_source(browser, source_names[addresses])
