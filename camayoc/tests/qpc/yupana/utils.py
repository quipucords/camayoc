# coding=utf-8
"""Utility functions for yupana tests."""


import base64
import json
import requests

from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError


def yupana_configs():
    """Return all of the yupana config values"""
    try:
        yupana_configs = get_config().get("yupana", [])
    except ConfigFileNotFoundError:
        yupana_configs = []
    return yupana_configs


def get_x_rh_identity(account_num, org_id):
    """Return the base64 encoded x-rh-identity string from credentials."""
    login_data = {
        "identity": {"account_number": account_num, "internal": {"org_id": org_id}}
    }
    print(login_data)
    json_str = json.dumps(login_data)
    print(json_str)
    return base64.b64encode(json_str.encode("ascii"))


def get_app_url(protocol="http://"):
    """Build and return the URI from the config to access the yupana API"""
    yupana_config = yupana_configs()
    config = yupana_config["yupana-app"]
    required_configs = (
        "app_name",
        "openshift_project",
        "openshift_app_domain",
        "api_path",
    )
    if set(required_configs).issubset(set(config.keys())):
        url = (
            protocol
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


def post_file(
    file_src,
    api_url,
    rh_username,
    rh_pass,
    x_rh_identity,
    x_rh_insights_request_id,
    file_type="application/vnd.redhat.qpc.tar+tgz",
):
    """Send a file/package up to the cluster."""

    headers = {
        "x-rh-insights-request-id": x_rh_insights_request_id,
        "x-rh-identity": x_rh_identity,
    }

    files = {"file": (file_src, open(file_src, "rb"), file_type)}
    api_endpoint = api_url + "/upload"
    response = requests.post(
        api_endpoint,
        headers=headers,
        files=files,
        auth=(rh_username, rh_pass),
        verify=False,
    )
    return response
