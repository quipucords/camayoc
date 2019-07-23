"""Pytest customizations and fixtures for yupana tests."""
import pytest

import oc
import time

from camayoc.tests.qpc.yupana.utils import (
    get_app_pods,
    get_x_rh_identity,
    post_file,
    time_diff,
)

from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError


@pytest.fixture(scope="class")
def yupana_config():
    """Return all of the yupana config values"""
    try:
        yupana_configs = get_config().get("yupana", [])
    except ConfigFileNotFoundError:
        yupana_configs = []
    return yupana_configs


@pytest.fixture(scope="class")
def mult_pod_logs(yupana_config):
    """Retrieves and returns the concatenated log outputs for multiple pods,
    within a defined time range."""
    upload_service_config = yupana_config["upload-service"]
    pod_names = [
        pod[0] for pod in get_app_pods(yupana_config["yupana-app"]["app_name"])
    ]
    start_time = time.time()
    response = post_file(
        upload_service_config["file_upload_src"],
        upload_service_config["api_url"],
        upload_service_config["rh_username"],
        upload_service_config["rh_password"],
        get_x_rh_identity(
            upload_service_config["rh_account_number"],
            upload_service_config["rh_org_id"],
        ),
        upload_service_config["rh_insights_request_id"],
    )
    assert response.status_code == 202, response.text

    ## Optional, give cluster some time to start
    time.sleep(30)
    ## Get recent logs from all pods
    pod_logs = [
        oc.logs(pod, since=f"{time_diff(start_time)}s", timestamps=True)
        for pod in pod_names
    ]
    return pod_logs
