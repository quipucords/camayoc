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

import requests

from camayoc.tests.qpc.yupana.utils import get_app_url, search_mult_pod_logs


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


def test_yupana_config(yupana_config):
    """Ensure the required yupana app configs are provided.

    :id: 94ed56dc-9f65-11e9-aaaf-8c1645a90ee2
    :description: Ensure that the required configs to test the yupana app are
        defined.
    :expectedresults: Configs should be defined in the 'yupana->yupana-app'
        section of the camayoc configuration file. Values should be supplied for
        each item defined in 'EXPECTED_APP_CONFIGS'.
    """
    assert yupana_config != []
    assert sorted(set(yupana_config["yupana-app"].keys())) == sorted(
        EXPECTED_APP_CONFIGS
    ), "Expected yupana app configs not properly provided."


def test_upload_service_config(yupana_config):
    """Ensure the required upload service configs are provided.

    :id: f44b7cda-9f65-11e9-8acb-8c1645a90ee2
    :description: Ensure that the required configs to test interacting with the
        upload service are defiend.
    :expectedresults: Configs should be defined in the 'yupana->yupana-app'
        section of the camayoc configuration file. Values should be supplied for
        each key item defined in 'EXPECTED_UPLOAD_SERVICE_CONFIGS'.
    """
    assert yupana_config != []
    assert sorted(set(yupana_config["upload-service"].keys())) == sorted(
        EXPECTED_UPLOAD_SERVICE_CONFIGS
    ), "Expected upload service configs not properly provided."


def test_connect(yupana_config, isolated_filesystem):
    """Test the connection to the desired cluster.

    :id: d94f7f5e-9f55-11e9-95da-8c1645a90ee2
    :description: Test that connection to the yupana application can be made.
    :expectedresults: At 200 status response should be recieved, indicating a
        successfull connection.
    """
    response = requests.get(get_app_url(yupana_config) + "status/")
    assert response.status_code == 200, response.text


class Test_Uploads:
    def test_upload(self, yupana_config, mult_pod_logs, isolated_filesystem):
        """Test uploading a file to the service.

        :id: 2bd03a02-9f56-11e9-b9ee-8c1645a90ee2
        :description: Test that a sample package can be uploaded to the upload
            service.
        :expectedresults: At 202 status response should be recieved, indicating a
            successfull transfer.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(pod_logs, "NEW REPORT UPLOAD")
        assert log_matches is not []
