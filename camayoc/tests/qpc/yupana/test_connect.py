# coding=utf-8
"""Tests for connecting to yupana and related cluster apps

:caseautomation: automated
:casecomponent: yupana
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""

import oc
import requests
import time

from camayoc.tests.qpc.yupana.utils import (
    get_app_url,
    get_app_pods,
    get_x_rh_identity,
    post_file,
    search_log,
    search_mult_pod_logs,
    time_diff,
    yupana_configs,
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
    """Ensure the required yupana app configs are provided.

    :id: 94ed56dc-9f65-11e9-aaaf-8c1645a90ee2
    :description: Ensure that the required configs to test the yupana app are
        defined.
    :expectedresults: Configs should be defined in the 'yupana->yupana-app'
        section of the camayoc configuration file. Values should be supplied for
        each item defined in 'EXPECTED_APP_CONFIGS'.
    """

    config = yupana_configs()
    assert config != []
    assert sorted(set(config["yupana-app"].keys())) == sorted(
        EXPECTED_APP_CONFIGS
    ), "Expected yupana app configs not properly provided."


def test_upload_service_config():
    """Ensure the required upload service configs are provided.

    :id: f44b7cda-9f65-11e9-8acb-8c1645a90ee2
    :description: Ensure that the required configs to test interacting with the
        upload service are defiend.
    :expectedresults: Configs should be defined in the 'yupana->yupana-app'
        section of the camayoc configuration file. Values should be supplied for
        each key item defined in 'EXPECTED_UPLOAD_SERVICE_CONFIGS'.
    """
    config = yupana_configs()
    assert sorted(set(config["upload-service"].keys())) == sorted(
        EXPECTED_UPLOAD_SERVICE_CONFIGS
    ), "Expected upload service configs not properly provided."


def test_connect(isolated_filesystem, sleep_time=30):
    """Test the connection to the desired cluster.

    :id: d94f7f5e-9f55-11e9-95da-8c1645a90ee2
    :description: Test that connection to the yupana application can be made.
    :expectedresults: At 200 status response should be recieved, indicating a
        successfull connection.
    """
    config = yupana_configs()
    pod_names = [pod[0] for pod in
                 get_app_pods(config['yupana-app']['app_name'])]
    start_time = time.time()
    response = requests.get(get_app_url() + "status/")
    assert response.status_code == 200, response.text
    ## Optional, give cluster some time to start
    time.sleep(sleep_time)
    ## Get recent logs from all pods
    pod_logs = [oc.logs(pod, since=f"{time_diff(start_time)}s", timestamps=True) for pod in
                pod_names]
    log_matches = search_mult_pod_logs(pod_logs, "ASSIGNING REPORT SLICE")
    assert log_matches is []

def test_upload(isolated_filesystem):
    """Test uploading a file to the service.

    :id: 2bd03a02-9f56-11e9-b9ee-8c1645a90ee2
    :description: Test that a sample package can be uploaded to the upload
        service.
    :expectedresults: At 202 status response should be recieved, indicating a
        successfull transfer.
    """
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
