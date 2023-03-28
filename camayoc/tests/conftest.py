# coding=utf-8
"""Pytest customizations and fixtures for the quipucords tests."""
import ssl
from pathlib import Path

import pytest
from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect

try:
    from pytest_ibutsu.pytest_plugin import ibutsu_plugin_key
    from pytest_ibutsu.pytest_plugin import ibutsu_result_key
except ImportError:
    ibutsu_plugin_key = None

from camayoc import utils
from camayoc.config import settings
from camayoc.config import get_config


def _ibutsu_enabled(config: pytest.Config) -> bool:
    if not ibutsu_plugin_key:
        return False
    ibutsu = config.stash.get(ibutsu_plugin_key, None)
    if ibutsu is None:
        return False
    return ibutsu.enabled


def _fill_ibutsu_result(item: pytest.Item):
    ibutsu_result = item.stash[ibutsu_result_key]
    component = ibutsu_result.metadata.get("component", None)
    if not component:
        testpath, _, _ = item.location
        testpath = Path(testpath).relative_to("camayoc/tests/qpc/")
        component = testpath.parts[0]
    ibutsu_result.component = component


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, items: list[pytest.Item], config: pytest.Config
) -> None:
    ibutsu_enabled = _ibutsu_enabled(config)
    if not ibutsu_enabled:
        return
    for item in items:
        _fill_ibutsu_result(item)


@pytest.fixture(scope="session")
def vcenter_client():
    """Create a vCenter client.

    The configuration in the Camayoc's configuration file should be as the
    following::

        vcenter:
          hostname: vcenter.domain.example.com
          username: gandalf
          password: YouShallNotPass

    Use standard dynaconf environment variable handling system to specify these
    settings through environment variables.
    """
    vcenter_host = settings.vcenter.hostname
    vcenter_user = settings.vcenter.username
    vcenter_pwd = settings.vcenter.password

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
