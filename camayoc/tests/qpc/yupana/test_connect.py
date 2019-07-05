"""Starting tests for configs"""

import requests

from camayoc.tests.qpc.yupana.utils import (
    yupana_configs,
    get_app_url,
    post_file,
    get_x_rh_identity,
)


EXPECTED_APP_CONFIGS = (
    "app_name",
    "openshift_project",
    "openshift_app_domain",
    "api_path",
)
EXPECTED_UPLOAD_SERVICE_CONFIGS = (
    "api_url",
    "rh_username",
    "rh_password",
    "rh_account_number",
    "rh_org_id",
    "file_upload_src",
    "rh_insights_request_id",
)


def test_yupana_config():
    """test load configurations"""
    config = yupana_configs()
    assert config != []
    assert sorted(set(config["yupana-app"].keys())) == sorted(
        EXPECTED_APP_CONFIGS
    ), "Expected yupana app configs not properly provided."


def test_upload_service_config():
    """test upload service config provided"""
    config = yupana_configs()
    assert sorted(set(config["upload-service"].keys())) == sorted(
        EXPECTED_UPLOAD_SERVICE_CONFIGS
    ), "Expected upload service configs not properly provided."


def test_connect():
    """Test the connection to the desired cluster."""
    response = requests.get(get_app_url() + "status/")
    assert response.status_code == 200, response.text


def test_upload():
    """Test uploading a file to the service."""
    yupana_config = yupana_configs()
    config = yupana_config["upload-service"]
    response = post_file(
        config["file_upload_src"],
        config["api_url"],
        config["rh_username"],
        config["rh_password"],
        get_x_rh_identity(config["rh_account_number"], config["rh_org_id"]),
        config["rh_insights_request_id"],
    )
    assert response.status_code == 202, response.text
