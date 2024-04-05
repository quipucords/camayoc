# coding=utf-8
"""Utility functions."""
import base64
import contextlib
import json
import os
import shutil
import tempfile
import uuid
from urllib.parse import urlunparse

from camayoc.config import settings
from camayoc.types.settings import ScanOptions

_XDG_ENV_VARS = ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")
"""Environment variables related to the XDG Base Directory specification."""

client_cmd = settings.quipucords_cli.executable
"""Client command to use during tests. Defaults to `qpc`."""

client_cmd_name = settings.quipucords_cli.display_name
"""Client name displayed on help texts. Defaults to `qpc`."""
# this is useful when client_cmd is set to an absolute path, has extra arguments like -v


def get_qpc_url():
    """Return the base url for the qpc server."""
    hostname = settings.quipucords_server.hostname
    scheme = "https" if settings.quipucords_server.https else "http"
    port = str(settings.quipucords_server.port)
    netloc = hostname + ":{}".format(port) if port else hostname
    return urlunparse((scheme, netloc, "", "", "", ""))


def uuid4():
    """Return a random UUID, as a unicode string."""
    return str(uuid.uuid4())


@contextlib.contextmanager
def isolated_filesystem(filesystem_path=None):
    """Context Manager that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    cwd = os.getcwd()
    path = tempfile.mkdtemp(dir=filesystem_path, prefix="")
    for envvar in _XDG_ENV_VARS:
        os.environ[envvar] = path
    os.chdir(path)
    try:
        yield path
    finally:
        for envvar in _XDG_ENV_VARS:
            del os.environ[envvar]
        os.chdir(cwd)
        try:
            shutil.rmtree(path)
        except (OSError, IOError):
            pass


def create_identity(account_number, org_id=None):
    """Base64-encoded JSON identity."""
    identity = {"identity": {"account_number": account_number}}
    if org_id is not None:
        identity["identity"]["internal"] = {"org_id": org_id}
    identity = json.dumps(identity)
    identity = base64.standard_b64encode(identity.encode("ascii"))
    identity = identity.decode("ascii")
    return identity


def create_x_rh_identity(account_number, org_id=None):
    """Base64-encoded JSON identity header provided by 3Scale."""
    identity = create_identity(account_number, org_id)
    x_rh_identity = {"x-rh-identity": identity}
    return x_rh_identity


def expected_data_has_attribute(scan_definition: ScanOptions, attr_name: str) -> bool:
    """Check if scan definition has an attribute in expected_data."""
    if not scan_definition.expected_data:
        return False
    for expected_data in scan_definition.expected_data.values():
        if getattr(expected_data, attr_name, None):
            return True
    return False
