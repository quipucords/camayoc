# coding=utf-8
"""Tests for ``Reports`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import csv
import json
from pprint import pformat

import pytest

from camayoc import api, utils
from camayoc.qpc_models import Report
from camayoc.tests.qpc.api.v1.conftest import SCAN_DATA
from camayoc.tests.qpc.api.v1.conftest import get_scan_result, scan_list
from camayoc.tests.qpc.utils import mark_runs_scans


def get_report_entity_src_ids(entity):
    """Given an entity from a deployment report, find the source ids."""
    entity_src_ids = []
    client = api.Client()
    for s in entity["sources"]:
        s_info = client.get("sources/?name={}".format(s["source_name"]))
        # the source is returned in a list, but there should only be one item
        # because names should be unique
        s_info = s_info.json().get("results", {})
        assert len(s_info) == 1
        s_info = s_info[0]
        if s_info.get("id"):
            entity_src_ids.append(s_info.get("id"))
    return entity_src_ids


def validate_csv_response(response):
    """Validate that the response provided is csv."""
    msg = 'Report is not expected content-type "csv".'
    try:
        csv_text = response.text
        csv.reader(csv_text, delimiter=",")
        deployments_csv = "Report\r\n" in csv_text
        details_csv = "Report,Number Sources\r\n" in csv_text
        assert deployments_csv or details_csv, msg + " Incorrect data format."
    except csv.Error:
        assert False, msg


def validate_json_response(response):
    """Validate that the response provided is json."""
    try:
        response.json()
    except json.JSONDecodeError:
        assert False, 'Report is not expected content-type "json".'


@mark_runs_scans
def test_report_content_consistency():
    """Confirm that a report is created with the correct content type.

    :id: 9724fb9a-c151-4288-a8d0-7238472731a8
    :description: If a scan job identifier is provided,
        a valid report of the given content type should be returned.
    :steps:
        1) Grab the scan info for a scan from SCAN_DATA
        2) Check if the scan info is None return if so
        3) Grab the scan job identifier from the scan info a scan
        4) Access the deployments & details endpoint of the report as JSON
        5) Access the deployments & details endpoint of the report as CSV
        6) Access the deployments & details endpoint of the report as JSON
        7) Access the deployments & details endpoint of the report as CSV
        8) Assert that all response codes were successful
    :expectedresults: Reports return the appropriate content type.
    """
    scan = SCAN_DATA.get("rhel-7")
    # if either scan is None, they were not in the config file or the
    # tests have been ran with RUN_SCANS=False and there are no scan results
    if scan is None:
        pytest.xfail(reason="Config file does not have " 'dependent scan "rhel-7".')
    scan_job_id = scan.get("scan_job_id")
    report = Report()
    response = report.retrieve_from_scan_job(scan_job_id)
    if response.json().get("report_id") is None:
        pytest.xfail(reason='Scan Job does not have "report_id".')
    accept_json = {"Accept": "application/json"}
    accept_csv = {"Accept": "text/csv"}

    validate_csv_response(report.details(headers=accept_csv))
    validate_json_response(report.details(headers=accept_json))
    validate_csv_response(report.details(headers=accept_csv))
    validate_json_response(report.details(headers=accept_json))

    validate_csv_response(report.deployments(headers=accept_csv))
    validate_json_response(report.deployments(headers=accept_json))
    validate_csv_response(report.deployments(headers=accept_csv))
    validate_json_response(report.deployments(headers=accept_json))


def assert_merge_fails(ids, errors_found, report):
    """Assert that the merge method on the given report fails.

    :param ids: The scan job identifiers to pass through to
        the merge function.
    :param report: The report object
    :param errors_found: A list of any errors encountered
    """
    # replace whatever client the report had with one that won't raise
    # exceptions
    orig_client = report.client
    report.client = api.Client(response_handler=api.echo_handler)
    merge_response = report.create_from_merge(ids)
    if merge_response.status_code != 400:
        errors_found.append(
            "Merging scan job identifiers {ids} resulted in a response"
            "status code of {response_status} when it should have resulted"
            "in a status code of 400.".format(
                ids=ids, response_status=merge_response.status_code
            )
        )
    # give the report its original client back
    report.client = orig_client
    return errors_found


@mark_runs_scans
def test_merge_reports_from_scanjob():
    """Confirm that a report is created from valid scan job identifiers.

    :id: 10c6b86a-4271-4b00-b9bb-4ff4a37bb02c
    :description: If two valid scan job identifiers are provided,
        a valid report identifier should be returned.
    :steps:
        1) Grab the scan info for the scans to merge from SCAN_DATA
        2) Check if the scan info is None for either scan and return if so
        3) Grab the scan job identifier from the scan info of each scan
        4) Create a report object & merge the scan job identifiers
        5) Access the deployments & details endpoint of the report
        6) Assert that all response codes were successful
    :expectedresults: Scan job results are merged into a report.
    """
    errors_found = []
    scan1 = SCAN_DATA.get("non-rhel")
    scan2 = SCAN_DATA.get("rhel-7")
    # if either scan is None, they were not in the config file or the
    # tests have been ran with RUN_SCANS=False and there are no scan results
    if scan1 is None or scan2 is None:
        pytest.xfail(
            reason="Config file does not have dependent scans "
            '"non-rhel" or "rhel-7".'
        )
    id1 = scan1.get("scan_job_id")
    id2 = scan2.get("scan_job_id")
    report = Report()
    response = report.create_from_merge([id1, id2])
    deployments = report.deployments()
    details = report.details()
    status_codes = [response.status_code, deployments.status_code, details.status_code]
    error = False
    for code in status_codes:
        if code not in range(200, 203):
            error = True
    if error:
        errors_found.append(
            "Merging scan jobs with identifiers: {scan1_id}, {scan2_id}"
            "resulted in a failed merge report. The report returned a status\n"
            "code of {report_status}. The deployments endpoint returned a"
            "status code of {deployments_status}. The details endpoint"
            "returned a status code of {details_status}.\n"
            "The full results from the first scan were: {s1}\n"
            "The full results from the second scan were: {s2}\n".format(
                scan1_id=id1,
                scan2_id=id2,
                report_status=response.status_code,
                deployments_status=deployments.status_code,
                details_status=details.status_code,
                s1=pformat(scan1),
                s2=pformat(scan2),
            )
        )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
def test_merge_reports_negative():
    """Confirm that merging invalid scan job ids does not result in a report.

    :id: 552e5de4-3697-11e8-b467-0ed5f89f718b
    :description: If a merge is attempted with invalid scan job identifiers,
        then report is not created.
    :steps:
        1) Create a list of invalid identifiers for merge requests
        2) Grab the connection scan from the SCAN_DATA
        3) Grab the unreachable scan from the SCAN_DATA
        4) Check that both the connection & unreachable scan exist
        5) If they do, grab the scan job identifiers and add them to the list
            of invalid identifiers
        6) Loop through the invalid ids and assert that each merge fails
    :expectedresults: A report is not created from invalid ids.
    """
    errors_found = []
    # create a list of invalid options for merging scan job identifiers
    invalid_ids = [[1], [1, 1], ["one", "one"], []]
    # attempt to grab the connection_scan & unreachable scan from data
    connection_scan = SCAN_DATA.get("Connection")
    unreachable_scan = SCAN_DATA.get("Unreachable")
    if connection_scan and unreachable_scan:
        # if the info was found, grab the ids from the data and add them
        # to the list of invalid identifiers
        connection_id = connection_scan.get("scan_job_id")
        unreachable_id = unreachable_scan.get("scan_job_id")
        invalid_ids.append([connection_id, unreachable_id])
    report = Report()
    # Loop through the invalid ids and assert that the merge fails
    for ids in invalid_ids:
        errors_found = assert_merge_fails(ids, errors_found, report)
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_products_found_deployment_report(scan_info):
    """Test that products reported as present are correct for the source.

    :id: d5d424bb-8183-4b60-b21a-1b4ed1d879c0
    :description: Test that products indicated as present are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that any products marked as present are expected to be found
           as is listed in the configuration file for the source.
    :expectedresults: There are inspection results for each source we scanned
        and any products found are correctly identified.
    """
    result = get_scan_result(scan_info["name"])
    report_id = result["report_id"]
    if not report_id:
        pytest.xfail(
            reason="No report id was returned from scan "
            "named {scan_name}".format(scan_name=scan_info["name"])
        )
    report = api.Client().get("reports/{}/deployments".format(report_id)).json()
    assert report.get("status") == "completed", report
    report = report.get("system_fingerprints")
    errors_found = []
    for entity in report:
        all_found_products = []
        present_products = []
        for product in entity.get("products"):
            name = "".join(product["name"].lower().split())
            if product["presence"] == "present":
                present_products.append(name)
            if product["presence"] in ["present", "potential"]:
                all_found_products.append(name)
        for source_to_product_map in result["expected_products"]:
            src_id = list(source_to_product_map.keys())[0]
            entity_src_ids = get_report_entity_src_ids(entity)
            hostname = result["source_id_to_hostname"][src_id]
            ex_products = source_to_product_map[src_id]
            expected_product_names = [
                prod for prod in ex_products.keys() if prod != "distribution"
            ]
            if src_id in entity_src_ids:
                # We assert that products marked as present are expected
                # We do not assert that products marked as potential must
                # actually be on server
                unexpected_products = []
                for prod_name in present_products:
                    # Assert that products marked "present"
                    # Are actually expected on machine
                    if prod_name not in expected_product_names:
                        unexpected_products.append(prod_name)
                # after inpsecting all found products,
                # raise assertion error for all unexpected products
                if len(unexpected_products) > 0:
                    errors_found.append(
                        "Found {found_products} but only expected to find\n"
                        "{expected_products} on {host_found_on}.\n"
                        "All information about the entity was as follows\n"
                        "{entity_info}".format(
                            found_products=unexpected_products,
                            expected_products=expected_product_names,
                            host_found_on=hostname,
                            entity_info=pformat(entity),
                        )
                    )
    assert len(errors_found) == 0, (
        "Found {num} unexpected products!\n"
        "Errors are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            num=len(errors_found),
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(result),
        )
    )


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_OS_found_deployment_report(scan_info):
    """Test that OS identified are correct for the source.

    :id: 0b16331c-2431-498a-9e84-65b3d66e4001
    :description: Test that OS type and version are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that the OS identified is expected to be found
           as is listed in the configuration file for the source.
    :expectedresults: There are inspection results for each source we scanned
        and the operating system is correctly identified.
    """
    result = get_scan_result(scan_info["name"])
    if scan_info["name"].lower() == 'sat6':
        pytest.mark.skip("Skipping sat6 run until Quipucords Issue #2039 "
                         "is resolved")

    report_id = result["report_id"]
    if not report_id:
        pytest.xfail(
            reason="No report id was returned from scan "
            "named {scan_name}".format(scan_name=scan_info["name"])
        )
    report = api.Client().get("reports/{}/deployments".format(report_id)).json()
    assert report.get("status") == "completed", report
    report = report.get("system_fingerprints")
    errors_found = []
    for entity in report:
        for source_to_product_map in result["expected_products"]:
            src_id = list(source_to_product_map.keys())[0]
            entity_src_ids = get_report_entity_src_ids(entity)
            hostname = result["source_id_to_hostname"][src_id]
            ex_products = source_to_product_map[src_id]
            expected_distro = ex_products["distribution"].get("name", "").lower()
            expected_version = ex_products["distribution"].get("version", "").lower()
            # The key may exist but the value be None
            if entity.get("os_name") is None:
                found_distro = ""
            else:
                found_distro = entity.get("os_name").lower()

            if entity.get("os_version") is None:
                found_version = ""
            else:
                found_version = entity.get("os_version").lower()

            if src_id in entity_src_ids:
                # We assert that the expected distro's name is at least
                # contained in the found name.
                # For example, if "Red Hat" is listed in config file,
                # It will pass if "Red Hat Enterprise Linux Server" is found
                if expected_distro not in found_distro:
                    errors_found.append(
                        "Expected OS named {0} for source {1} but"
                        "found OS named {2}".format(
                            expected_distro, hostname, found_distro
                        )
                    )
                # We assert that the expected distro's version is at least
                # contained in the found version.
                # For example, if "6.9" is listed in config file,
                # It will pass if "6.9 (Santiago)" is found
                if expected_version not in found_version:
                    errors_found.append(
                        "Expected OS version {0} for source {1} but"
                        "found OS version {2}".format(
                            expected_version, hostname, found_version
                        )
                    )

    assert len(errors_found) == 0, (
        "Found {num} unexpected OS names and/or versions!\n"
        "Errors are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            num=len(errors_found),
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(result),
        )
    )
