# coding=utf-8
"""Unit tests for :mod:`camayoc.utils`."""
import os

from tempfile import mkdtemp
from unittest import mock

import pytest

from camayoc import exceptions, utils


def test_run_scans():
    """Test the RUN_SCANS variable is correctly detected.

    This environment variable allows users to disable tests that run
    scans temporarily.
    """
    os.environ["RUN_SCANS"] = "FALSE"
    assert utils.run_scans() is False
    os.environ.pop("RUN_SCANS")
    assert utils.run_scans() is True
    os.environ["RUN_SCANS"] = "True"
    assert utils.run_scans() is True


def test_get_qpc_url():
    """Test ``camayoc.utils.get_qpc_url``."""
    with mock.patch("camayoc.utils.get_config") as get_config:
        get_config.return_value = {
            "qpc": {"hostname": "server.example.com", "https": True, "port": 443}
        }
        assert utils.get_qpc_url() == "https://server.example.com:443"


def test_get_qpc_url_no_hostname():
    """Test ``camayoc.utils.get_qpc_url`` when no hostname is present."""
    with mock.patch("camayoc.utils.get_config") as get_config:
        get_config.return_value = {"qpc": {"https": True, "port": 443}}
        with pytest.raises(exceptions.QPCBaseUrlNotFound) as err:
            utils.get_qpc_url()
        assert (
            'Make sure you have a "qpc" section and `hostname`is specified in '
            "the camayoc config file"
        ) in str(err.value)


def test_isolated_filesystem():
    """Test default ``camayoc.utils.isolated_filesystem``."""
    with utils.isolated_filesystem() as path:
        assert path.startswith("/tmp/") or path.startswith("/var/folders/"), (
            "Make sure default isolated_filesystem " "creates the temp dir at '/tmp/'."
        )


def test_isolated_filesystem_w_path():
    """Test ``camayoc.utils.isolated_filesystem`` with a provided
    filesystem_path."""
    test_path = mkdtemp(prefix="")
    with utils.isolated_filesystem(test_path) as path:
        assert path.startswith(test_path), (
            "Make sure isolated_filesystem "
            "creates the temp dir under ``filesystem_path``, when provided."
        )
