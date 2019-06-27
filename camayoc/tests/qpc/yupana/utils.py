# coding=utf-8
"""Utility functions for yupana tests."""


from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError, WaitTimeError


def yupana_configs():
    """Return all of the yupana config values"""
    try:
        yupana_configs = get_config().get("yupana", [])
    except ConfigFileNotFoundError:
        yupana_configs = []
    return yupana_configs


def get_api_url():
    """Build and return the URI from the config to access the yupana API"""
    config = yupana_configs()
    required_configs = (
        "app_name",
        "openshift_project",
        "openshift_app_domain",
        "api_path",
    )
    if set(required_configs).issubset(set(config.keys())):
        url = (
            "http://"
            + config["app_name"]
            + "-"
            + config["openshift_project"]
            + "."
            + config["openshift_app_domain"]
            + config["api_path"]
        )
        return url
    else:
        return None
