# coding=utf-8
"""Unit tests for :mod:`camayoc.utils`."""

from tempfile import mkdtemp
from unittest import mock

from camayoc import utils
from camayoc.types.settings import QuipucordsServerOptions
from camayoc.types.settings import ScanOptions


def test_get_qpc_url():
    """Test ``camayoc.utils.get_qpc_url``."""
    config = QuipucordsServerOptions(
        hostname="server.example.com",
        https=True,
        port=443,
        username="admin",
        password="pass",
        ssh_keyfile_path="/tmp/",
    )
    with mock.patch.object(utils, "settings") as get_config:
        get_config.quipucords_server = config
        assert utils.get_qpc_url() == "https://server.example.com:443"


def test_isolated_filesystem():
    """Test default ``camayoc.utils.isolated_filesystem``."""
    with utils.isolated_filesystem() as path:
        assert path.startswith("/tmp/") or path.startswith(
            "/var/folders/"
        ), "Make sure default isolated_filesystem creates the temp dir at '/tmp/'."


def test_isolated_filesystem_w_path():
    """Test ``camayoc.utils.isolated_filesystem`` with a provided filesystem_path."""
    test_path = mkdtemp(prefix="")
    with utils.isolated_filesystem(test_path) as path:
        assert path.startswith(test_path), (
            "Make sure isolated_filesystem "
            "creates the temp dir under ``filesystem_path``, when provided."
        )


def test_expected_data_has_attribute_happy_path():
    scan = ScanOptions(
        **{
            "name": "networkscan",
            "sources": ["mynetwork"],
            "expected_data": {
                "host1": {
                    "distribution": {
                        "name": "Fedora",
                        "version": "40",
                        "release": "",
                        "is_redhat": False,
                    }
                }
            },
        }
    )
    assert utils.expected_data_has_attribute(scan, "distribution")


def test_expected_data_has_attribute_no_attr():
    scan = ScanOptions(
        **{
            "name": "networkscan",
            "sources": ["mynetwork"],
            "expected_data": {
                "host1": {
                    "distribution": {
                        "name": "Fedora",
                        "version": "40",
                        "release": "",
                        "is_redhat": False,
                    }
                }
            },
        }
    )
    assert not utils.expected_data_has_attribute(scan, "products")


def test_expected_data_has_attribute_no_expected_data():
    scan = ScanOptions(
        **{
            "name": "networkscan",
            "sources": ["mynetwork"],
        }
    )
    assert not utils.expected_data_has_attribute(scan, "distribution")
