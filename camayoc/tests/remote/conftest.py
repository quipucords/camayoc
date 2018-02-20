# coding=utf-8
"""Fixtures for tests that use remote infrastructure."""

import ssl
import os

import pytest
from pyVim.connect import SmartConnect, Disconnect

from camayoc.config import get_config


@pytest.fixture(scope='module')
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
