# coding=utf-8
"""Utility functions."""

import contextlib
import os
import shutil
import tempfile
import uuid
from pathlib import Path
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


def expected_data_has_attribute(scan_definition: ScanOptions, attr_name: str) -> bool:
    """Check if scan definition has an attribute in expected_data."""
    if not scan_definition.expected_data:
        return False
    for expected_data in scan_definition.expected_data.values():
        if getattr(expected_data, attr_name, None):
            return True
    return False


def server_container_ssh_key_content(container_path: str):
    ssh_key_filename = Path(container_path).relative_to("/sshkeys/")
    for product_name in ("quipucords", "discovery"):
        # FIXME: could/should we re-purpose settings.quipucords_server.ssh_keyfile_path ?
        ssh_dir = f"~/.local/share/{product_name}/sshkeys/"
        ssh_key_path = Path(ssh_dir).expanduser().resolve() / ssh_key_filename
        try:
            return ssh_key_path.read_text()
        except OSError:
            continue
    msg = f"SSH file not found in local file system: {ssh_key_filename}"
    raise OSError(msg)
