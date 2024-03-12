# coding=utf-8
"""Tools for managing information about test systems.

Camayoc needs to know what servers it can talk to and how to access those
systems. For example, it needs to know the username, hostname and password of a
system in order to SSH into it.
"""
import os
import warnings

from dynaconf import Dynaconf
from dynaconf import Validator
from xdg import BaseDirectory

from camayoc import exceptions
from camayoc.types.settings import Configuration

default_dynaconf_validators = [
    Validator("camayoc.run_scans", default=False),
    Validator("quipucords_server.hostname", default=""),
    Validator("quipucords_server.https", default=False),
    Validator("quipucords_server.port", default=8000),
    Validator("quipucords_server.ssl_verify", default=False),
    Validator("quipucords_server.username", default=""),
    Validator("quipucords_server.password", default=""),
    Validator("quipucords_server.ssh_keyfile_path", default=""),
    Validator("quipucords_cli.executable", default="qpc"),
    Validator("quipucords_cli.display_name", default="qpc"),
    Validator("credentials", default=[]),
    Validator("sources", default=[]),
    Validator("scans", default=[]),
]


def get_settings_files(xdg_config_dir, xdg_config_file):
    """Search ``XDG_CONFIG_DIRS`` for a config file and return all found.

    Search each of the standard XDG configuration directories for a
    configuration file. Return a list of all that have been found.
    The list is ordered from system-wide to user-specific. That's because
    result of this function is fed to Dynaconf, and Dynaconf reads all
    provided files in order, with values in latter file shadowing values
    from earlier file.

    May issue the warning if none of the paths exist. Dynaconf will still
    read configuration from environment variables, so missing files are
    generally not fatal.

    :param xdg_config_dir: A string. The name of the directory that is suffixed
        to the end of each of the ``XDG_CONFIG_DIRS`` paths.
    :param xdg_config_file: A string. The name of the configuration file that
        is being searched for.
    :returns: A list of strings. Each item is a path to existing configuration
        file.
    """
    settings_files = list(BaseDirectory.load_config_paths(xdg_config_dir, xdg_config_file))[::-1]

    if not settings_files:
        searched_paths = reversed(
            [
                os.path.join(config_dir, xdg_config_dir, xdg_config_file)
                for config_dir in BaseDirectory.xdg_config_dirs
            ]
        )
        msg = (
            "Camayoc is unable to find a configuration file. The following "
            "(XDG compliant) paths have been searched: {}\n"
            "This is generally not a problem, as Camayoc can read configuration "
            "from environment variables. But you might encounter exceptions later."
        ).format(", ".join(searched_paths))
        warnings.warn(msg, exceptions.ConfigFileNotFoundError)
    return settings_files


def get_settings(path=None) -> Configuration:
    if not path:
        settings_files = get_settings_files("camayoc", "config.yaml")
        dynaconf_validators = default_dynaconf_validators
    else:
        settings_files = [path]
        dynaconf_validators = []

    raw_settings = Dynaconf(
        settings_files=settings_files,
        validators=dynaconf_validators,
    )

    to_validate_settings = {key.lower(): value for key, value in raw_settings.as_dict().items()}

    validated_settings = Configuration(**to_validate_settings)

    return validated_settings


settings = get_settings()


def get_config():
    """Backwards compatibility shim. Returns global config object."""
    shim_settings = settings.dict(by_alias=True)
    qpc_options = shim_settings.pop("quipucords_server")
    shim_settings["qpc"] = qpc_options
    return shim_settings
