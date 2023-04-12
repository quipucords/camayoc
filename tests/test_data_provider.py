from unittest import mock

import pytest

from camayoc.data_provider import DataProvider
from camayoc.exceptions import NoMatchingDataDefinitionException
from camayoc.types.settings import ScanOptions
from camayoc.types.settings import SourceOptions
from camayoc.types.settings import SSHNetworkCredentialOptions
from camayoc.types.settings import VCenterCredentialOptions


CREDENTIALS = [
    SSHNetworkCredentialOptions(
        **{
            "name": "network",
            "type": "network",
            "username": "root",
            "sshkeyfile": "~/.ssh/id_rsa",
        }
    ),
    VCenterCredentialOptions(
        **{
            "name": "vcenter",
            "type": "vcenter",
            "password": "example1",
            "username": "username1",
        }
    ),
]
SOURCES = [
    SourceOptions(
        **{
            "name": "mynetwork",
            "hosts": ["myfavnetwork.com"],
            "credentials": ["network"],
            "type": "network",
        }
    ),
    SourceOptions(
        **{
            "name": "vcenter",
            "hosts": ["my_vcenter.com"],
            "credentials": ["vcenter"],
            "type": "vcenter",
            "options": {"ssl_cert_verify": False},
        }
    ),
]
SCANS = [
    ScanOptions(
        **{
            "name": "networkscan",
            "sources": ["mynetwork"],
        }
    ),
    ScanOptions(
        **{
            "name": "VCenterOnly",
            "sources": ["vcenter"],
        }
    ),
]


def test_defined_one():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_create:
            cred = dp.credentials.defined_one({"type": "network"})
            mock_create.assert_called_once()
    assert cred.name == "network"
    assert cred.username == "root"
    assert cred.ssh_keyfile == "~/.ssh/id_rsa"


def test_defined_reuse():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_create:
            cred1 = dp.credentials.defined_one({"type": "network"})
            cred2 = dp.credentials.defined_one({"type": "network"})
            mock_create.assert_called_once()
    assert cred1.name == "network"
    assert cred1.username == "root"
    assert cred1.ssh_keyfile == "~/.ssh/id_rsa"
    assert cred1.equivalent(cred2)


def test_new_one():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_create:
            cred = dp.credentials.new_one({"type": "network"}, data_only=False)
            mock_create.assert_called_once()
    assert cred.name != "network"
    assert cred.username == "root"
    assert cred.ssh_keyfile == "~/.ssh/id_rsa"


def test_new_one_data_only():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_create:
            cred = dp.credentials.new_one({"type": "network"}, data_only=True)
            mock_create.assert_not_called()
    assert cred.name != "network"
    assert cred.username == "root"
    assert cred.ssh_keyfile == "~/.ssh/id_rsa"


def test_new_with_dependencies():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_cred_create:
            with mock.patch.object(dp.sources._model_class, "create") as mock_source_create:
                source1 = dp.sources.new_one(
                    {"type": "network"}, new_dependencies=True, data_only=False
                )
                source2 = dp.sources.new_one(
                    {"type": "network"}, new_dependencies=True, data_only=False
                )
                assert mock_cred_create.call_count == 2
                assert mock_source_create.call_count == 2
    assert len(dp.credentials._created_models) == 2
    assert source1.name != "mynetwork"
    assert source1.name.startswith("mynetwork")
    assert source2.name.startswith("mynetwork")


def test_new_without_dependencies():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "create") as mock_cred_create:
            with mock.patch.object(dp.sources._model_class, "create") as mock_source_create:
                source1 = dp.sources.new_one(
                    {"type": "network"}, new_dependencies=False, data_only=False
                )
                source2 = dp.sources.new_one(
                    {"type": "network"}, new_dependencies=False, data_only=False
                )
                mock_cred_create.assert_called_once()
                assert mock_source_create.call_count == 2
    assert len(dp.credentials._created_models) == 1
    assert source1.name != "mynetwork"
    assert source1.name.startswith("mynetwork")
    assert source2.name.startswith("mynetwork")


def test_new_no_match():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with pytest.raises(NoMatchingDataDefinitionException):
        dp.credentials.new_one({"nosuchkey": "nosuchvalue"})


def test_automatic_cleanup():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "delete") as mock_delete:
            dp.credentials.new_one({"type": "network"}, data_only=False)
            mock_delete.return_value = mock.Mock
            mock_delete.return_value.status_code = mock.PropertyMock(return_value=200)
            dp.cleanup()
            mock_delete.assert_called()


def test_mark_for_cleanup():
    dp = DataProvider(credentials=CREDENTIALS, sources=SOURCES, scans=SCANS)
    with mock.patch("camayoc.api.Client"):
        with mock.patch.object(dp.credentials._model_class, "delete") as mock_delete:
            cred = dp.credentials.new_one({"type": "network"}, data_only=True)
            mock_delete.return_value = mock.Mock
            mock_delete.return_value.status_code = mock.PropertyMock(return_value=200)
            dp.cleanup()
            mock_delete.assert_not_called()
            dp.mark_for_cleanup(cred)
            dp.cleanup()
            mock_delete.assert_called()
