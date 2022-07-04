"""Pytest customizations and fixtures for yupana tests."""
import pytest

import oc
import time

from camayoc.tests.qpc.yupana.utils import (
    get_app_pods,
    post_file,
    time_diff,
)

from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.utils import create_identity


@pytest.fixture(scope="session")
def yupana_config():
    """Return all of the yupana config values."""
    try:
        yupana_configs = get_config().get("yupana", [])
    except ConfigFileNotFoundError:
        yupana_configs = []
    return yupana_configs


@pytest.fixture(scope="session")
def oc_setup(yupana_config):
    """Login to the cluster with oc."""
    oc_config = yupana_config["oc"]
    app_config = yupana_config["yupana-app"]
    login_response = oc.login(oc_config["url"], oc_config["token"])
    project_response = oc.set_project(app_config["openshift_project"])
    return (login_response, project_response)


@pytest.fixture(scope="class")
def mult_pod_logs(yupana_config):
    """Concatenate log outputs for multiple pods.

    Retrieves and returns the concatenated log outputs for multiple pods,
    within a defined time range.
    """
    upload_service_config = yupana_config["upload-service"]
    pod_names = [pod[0] for pod in get_app_pods(yupana_config["yupana-app"]["app_name"])]
    rh_identity = create_identity(
        upload_service_config["rh_account_number"], upload_service_config["rh_org_id"]
    )
    start_time = time.time()
    response = post_file(
        upload_service_config["file_upload_src"],
        upload_service_config["api_url"],
        upload_service_config["rh_username"],
        upload_service_config["rh_password"],
        rh_identity,
        upload_service_config["rh_insights_request_id"],
    )
    assert response.status_code == 202, response.text

    # Optional, give cluster some time to start
    time.sleep(30)
    # Get recent logs from all pods
    pod_logs = [
        oc.logs(pod, since=f"{time_diff(start_time)}s", timestamps=True) for pod in pod_names
    ]
    return pod_logs
