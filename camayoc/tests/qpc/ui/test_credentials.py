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
from pathlib import Path

import pytest

from camayoc import utils

from .utils import (
        check_auth_type,
        create_credential,
        delete_credential,
)

CREDENTIAL_TYPES = ['Network', 'Satellite', 'VCenter']


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
    delete_credential(browser, {name})


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
    delete_credential(browser, {name})


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
    delete_credential(browser, {name})


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
    delete_credential(browser, {name})
