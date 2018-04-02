# coding=utf-8
"""Pytest customizations and fixtures for the quipucords tests."""
import os
import ssl

from pyVim.connect import Disconnect, SmartConnect

import pytest

from camayoc import utils
from camayoc.config import get_config


@pytest.fixture(scope='session')
def vcenter_client():
    """Create a vCenter client.

    Get the client confifuration from environment variables and Camayoc's
    configuration file in this order. Raise a KeyError if can't find the
    expecting configuration.

    The expected environment variables are VCHOSTNAME, VCUSER and VCPASS for
    vcenter's hostname, username and password respectively.

    The configuration in the Camayoc's configuration file should be as the
    following::

        vcenter:
          hostname: vcenter.domain.example.com
          username: gandalf
          password: YouShallNotPass

    The vcenter config can be mixed by using both environement variables and
    the configuration file but environment variable takes precedence.
    """
    config = get_config()
    vcenter_host = os.getenv('VCHOSTNAME', config['vcenter']['hostname'])
    vcenter_user = os.getenv('VCUSER', config['vcenter']['username'])
    vcenter_pwd = os.getenv('VCPASS', config['vcenter']['password'])

    try:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
        )
    except ssl.SSLError:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
            sslContext=ssl._create_unverified_context(),
        )
    yield c
    Disconnect(c)


@pytest.fixture
def isolated_filesystem():
    """Fixture that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    with utils.isolated_filesystem() as path:
        yield path
