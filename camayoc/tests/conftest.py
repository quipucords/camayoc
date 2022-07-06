# coding=utf-8
"""Pytest customizations and fixtures for the quipucords tests."""
import os
import ssl

import pytest
from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect

from camayoc import utils
from camayoc.config import get_config


@pytest.fixture(scope="session")
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
    vcenter_host = os.getenv("VCHOSTNAME", config["vcenter"]["hostname"])
    vcenter_user = os.getenv("VCUSER", config["vcenter"]["username"])
    vcenter_pwd = os.getenv("VCPASS", config["vcenter"]["password"])

    try:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
            connectionPoolTimeout=-1,
        )
    except ssl.SSLError:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
            sslContext=ssl._create_unverified_context(),
            connectionPoolTimeout=-1,
        )
    yield c
    Disconnect(c)


@pytest.fixture
def isolated_filesystem(request):
    """Fixture that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    # Create isolated filesystem directory in the ssh_keyfile_path
    # configuration location if marked with `ssh_keyfile_path`.
    mark = request.node.get_closest_marker("ssh_keyfile_path")
    ssh_keyfile_path = None
    if mark:
        cfg = get_config().get("qpc", {})
        ssh_keyfile_path = cfg.get("ssh_keyfile_path")
        if not ssh_keyfile_path:
            pytest.fail("QPC configuration 'ssh_keyfile_path' not provided or " "found")
    with utils.isolated_filesystem(ssh_keyfile_path) as path:
        yield path
