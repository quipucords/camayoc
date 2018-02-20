# coding=utf-8
"""Utility functions."""
import contextlib
import os
import shutil
import tempfile
import uuid
from urllib.parse import urlunparse

from camayoc import exceptions
from camayoc.config import get_config


_XDG_ENV_VARS = ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME')
"""Environment variables related to the XDG Base Directory specification."""


def get_qcs_url():
    """Return the base url for the qcs server."""
    cfg = get_config().get('qcs', {})
    hostname = cfg.get('hostname')

    if not hostname:
        raise exceptions.QCSBaseUrlNotFound(
            'Make sure you have a "qcs" section and `hostname`is specified in '
            'the camayoc config file'
        )

    scheme = 'https' if cfg.get('https', False) else 'http'
    port = str(cfg.get('port', ''))
    netloc = hostname + ':{}'.format(port) if port else hostname
    return urlunparse((scheme, netloc, '', '', '', ''))


def uuid4():
    """Return a random UUID, as a unicode string."""
    return str(uuid.uuid4())


@contextlib.contextmanager
def isolated_filesystem():
    """Context Manager that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    cwd = os.getcwd()
    path = tempfile.mkdtemp()
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
