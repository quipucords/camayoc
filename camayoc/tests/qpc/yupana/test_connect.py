"""Starting tests for configs"""

import requests

from camayoc.tests.qpc.yupana.utils import (
    yupana_configs,
    get_app_url,
    post_file,
    get_x_rh_identity,
)


EXPECTED_CONFIGS = ("app_name", "openshift_project", "openshift_app_domain", "api_path")


def test_config():
    """test load configurations"""
    config = yupana_configs()
    assert config != []
    assert sorted(set(config["yupana-app"].keys())) == sorted(EXPECTED_CONFIGS)


def test_connect():
    """Test the connection to the desired cluster."""
    request = requests.get(get_app_url() + "status/")
    assert request.status_code == 200


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
    assert response.status_code == 202
