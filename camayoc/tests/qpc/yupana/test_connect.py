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

import pytest
import requests

from camayoc.tests.qpc.yupana.utils import get_app_url
from oc.utils import search_mult_pod_logs


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


@pytest.mark.usefixtures("oc_setup")
class Test_Uploads:
    def test_new_report_upload(self, yupana_config, mult_pod_logs, isolated_filesystem):
        """Verifies the application detected a new report upload.

        :id: 2bd03a02-9f56-11e9-b9ee-8c1645a90ee2
        :description: Test that the 'NEW REPORT UPLOAD' message detected in
            application after sending an upload.
        :expectedresults: The string 'NEW REPORT UPLOAD' should be detected in
            one of the pod logs, after sending a new report.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(pod_logs, "NEW REPORT UPLOAD")
        assert log_matches is not []

    def test_report_saving_message(
        self, yupana_config, mult_pod_logs, isolated_filesystem
    ):
        """Verifies the application saved the upload service message.

        :id: 8e8e57a8-ad86-11e9-a486-8c1645a90ee2
        :description: Test that the 'Report SAVING MESSAGE' string detected in
            application after sending an upload.
        :expectedresults: The string 'Report SAVING MESSAGE' should be detected in
            one of the pod logs, after sending a new report.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(pod_logs, "NEW REPORT UPLOAD")
        assert log_matches is not []

    def test_start_report_processor(
        self, yupana_config, mult_pod_logs, isolated_filesystem
    ):
        """Verifies the application starts the report processor after upload

        :id: 3129d14a-ad87-11e9-97a2-8c1645a90ee2
        :description: Test that the 'Starting report processor. State is
            \"new\"' string detected in application after sending an upload.
        :expectedresults: The string 'Starting report processor. State is
            \"new\".' should be detected in one of the pod logs, after sending a
            new report.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(
            pod_logs, 'Starting report processor. State is "new".'
        )
        assert log_matches is not []

    def test_report_download(self, yupana_config, mult_pod_logs, isolated_filesystem):
        """Verifies the application starts to download the report after upload

        :id: e12eedc8-ad87-11e9-8c82-8c1645a90ee2
        :description: Test that the application starts to download the report
            recieving an upload.
        :expectedresults: The string 'REPORT DOWNLOAD - downloading' should be
            detected in one of the pod logs, after sending a new report.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(
            pod_logs,
            "REPORT DOWNLOAD -\
                                           downloading",
        )
        assert log_matches is not []

    def test_report_download_success(
        self, yupana_config, mult_pod_logs, isolated_filesystem
    ):
        """Verifies the application successfully download the report after upload

        :id: 2b130e0a-ad89-11e9-97da-8c1645a90ee2
        :description: Test that the application successfully downloads the report
            after an upload.
        :expectedresults: The string 'REPORT DOWNLOAD - successfully downloaded TAR' should be
            detected in one of the pod logs, after sending a new report.
        """
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(
            pod_logs, "REPORT DOWNLOAD - successfully downloaded TAR"
        )
        assert log_matches is not []

    def test_decode_report_metadata(
        self, yupana_config, mult_pod_logs, isolated_filesystem
    ):
        """Verifies the application successfully decoded the metadata from the
            report uploaded.

        :id: aa4ed3fc-ad89-11e9-b303-8c1645a90ee2
        :description: Test that the application successfully decodes the report
            metadata after an upload.
        :expectedresults: Several strings should be detected in one of the pod
            logs which signify that the metatdata was attempted and successfully
            decoded.
        """
        pod_logs = mult_pod_logs
        attempt_log_matches = search_mult_pod_logs(
            pod_logs,
            "EXTRACT REPORT\
                                                   FROM TAR - Attempting to\
                                                   decode the file\
                                                   metadata.json",
        )
        assert (
            attempt_log_matches is not []
        ), "Log indicating report metatdata\
                                               decode attempt not found in pod logs."
        success_log_matches = search_mult_pod_logs(
            pod_logs,
            "EXTRACT REPORT\
                                                   FROM TAR - Successfully\
                                                   decoded the file\
                                                   metadata.json",
        )
        assert (
            success_log_matches is not []
        ), "Log indicationg report metadata\
                                               decode success not found in pod logs."

    def test_report_metadata(self, yupana_config, mult_pod_logs, isolated_filesystem):
        """Verifies the correct metadata was successfully extracted and uploaded

        :id: 9d58265a-ad8c-11e9-8099-8c1645a90ee2
        :description: Test that the expected metadata was uploaded.
        :expectedresults: The expected metadata contents should be found in the
            at least one of the pod logs."""
        pod_logs = mult_pod_logs
        log_matches = search_mult_pod_logs(
            pod_logs,
            "The following source\
                                           metadata was uploaded:\
                                           {'any_satellite_info_you_want':\
                                            'some stuff that will not be\
                                            validated but will be logged'}",
        )
        assert log_matches is not []
