# coding=utf-8
"""Tests for ``Reports`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
import warnings
from pprint import pformat

import pytest

from camayoc import utils
from camayoc.qpc_models import Report
from camayoc.qpc_models import ScanJob
from camayoc.tests.qpc.api.v1.conftest import scan_list
from camayoc.tests.qpc.api.v1.utils import wait_until_state
from camayoc.types.settings import ScanOptions


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_info", scan_list(["network"]), ids=utils.name_getter)
def test_products_found_deployment_report(data_provider, scan_info: ScanOptions):
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
    scan = data_provider.scans.defined_one({"name": scan_info.name})
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, state="stopped")
    report = Report()
    report.retrieve_from_scan_job(scan_job_id=scanjob._id)
    if not report._id:
        pytest.xfail(
            reason="No report id was returned from scan "
            "named {scan_name}".format(scan_name=scan_info.name)
        )
    report_content = report.deployments().json()
    assert report_content.get("status") == "completed"
    system_fingerprints = report_content.get("system_fingerprints")
    found_hosts = {host.get("name"): host for host in system_fingerprints}
    if len(found_hosts) != len(system_fingerprints):
        msg = "Some discovered hosts have the same name. " "Test result might not be accurate."
        warnings.warn(msg)
    errors_found = []
    for hostname, expected_data in scan_info.expected_data.items():
        if not (expected_products := expected_data.products):
            continue
        if not found_hosts.get(hostname):
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_info.name}, but not found"
            )
        for fingerprint in system_fingerprints:
            present_product_names = {
                product["name"]
                for product in fingerprint.get("products")
                if product["presence"] == "present"
            }
            expected_product_names = {
                product.name for product in expected_products if product.presence == "present"
            }
            unexpected_product_names = {
                product_name
                for product_name in present_product_names
                if product_name not in expected_product_names
            }
            if len(unexpected_product_names) > 0:
                errors_found.append(
                    "Found {found_products} but only expected to find\n"
                    "{expected_products} on {host_found_on}.\n"
                    "All information about the fingerprint was as follows\n"
                    "{fingerprint_info}".format(
                        found_products=unexpected_product_names,
                        expected_products=expected_product_names,
                        host_found_on=hostname,
                        fingerprint_info=pformat(fingerprint),
                    )
                )
    assert len(errors_found) == 0, (
        "Found {num} unexpected products!\n"
        "Errors are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            num=len(errors_found),
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(report_content),
        )
    )


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_OS_found_deployment_report(data_provider, scan_info: ScanOptions):
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
    scan = data_provider.scans.defined_one({"name": scan_info.name})
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, state="stopped")
    report = Report()
    report.retrieve_from_scan_job(scan_job_id=scanjob._id)
    if not report._id:
        pytest.xfail(
            reason="No report id was returned from scan "
            "named {scan_name}".format(scan_name=scan_info.name)
        )
    report_content = report.deployments().json()
    assert report_content.get("status") == "completed", report
    system_fingerprints = report_content.get("system_fingerprints")
    found_hosts = {}
    for host in system_fingerprints:
        found_hosts[host.get("name")] = host
    if len(found_hosts) != len(system_fingerprints):
        msg = "Some discovered hosts have the same name. " "Test result might not be accurate."
        warnings.warn(msg)

    errors_found = []
    for hostname, expected_data in scan_info.expected_data.items():
        expected_distribution = expected_data.distribution
        if not expected_distribution:
            continue

        actual_data = found_hosts.get(hostname)
        if not actual_data:
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_info.name}, but not found"
            )

        found_release = actual_data.get("os_release", "")
        if found_release is None:
            found_release = ""
        found_distro = actual_data.get("os_name", "")
        if found_distro is None:
            found_distro = ""
        found_version = str(actual_data.get("os_version", ""))
        if found_version is None:
            found_version = ""

        if expected_distribution.release not in found_release:
            errors_found.append(
                "Expected OS release {0} for host {1} but"
                "found OS release {2}".format(
                    expected_distribution.release,
                    hostname,
                    found_release,
                )
            )

        # We assert that the expected distro's name is at least
        # contained in the found name.
        # For example, if "Red Hat" is listed in config file,
        # It will pass if "Red Hat Enterprise Linux Server" is found
        if expected_distribution.name not in found_distro:
            errors_found.append(
                "Expected OS named {0} for source {1} but"
                "found OS named {2}".format(
                    expected_distribution.name,
                    hostname,
                    found_distro,
                )
            )
        # We assert that the expected distro's version is at least
        # contained in the found version.
        # For example, if "6.9" is listed in config file,
        # It will pass if "6.9 (Santiago)" is found
        if expected_distribution.version not in found_version:
            errors_found.append(
                "Expected OS version {0} for source {1} but"
                "found OS version {2}".format(
                    expected_distribution.version,
                    hostname,
                    found_version,
                )
            )

    assert len(errors_found) == 0, (
        "Found {num} unexpected OS names and/or versions!\n"
        "Errors are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            num=len(errors_found),
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(report_content),
        )
    )
