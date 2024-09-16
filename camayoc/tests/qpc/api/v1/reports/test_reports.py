# coding=utf-8
"""Tests for ``Reports`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import warnings
from functools import partial
from pprint import pformat

import pytest

from camayoc.tests.qpc.utils import scan_names
from camayoc.utils import expected_data_has_attribute

SENTINEL = object()

has_product = partial(expected_data_has_attribute, attr_name="products")
has_distribution = partial(expected_data_has_attribute, attr_name="distribution")
has_installed_products = partial(expected_data_has_attribute, attr_name="installed_products")
has_raw_facts = partial(expected_data_has_attribute, attr_name="raw_facts")
has_aggregate = partial(expected_data_has_attribute, attr_name="aggregate")


@pytest.mark.slow
@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", scan_names(has_product))
def test_products_found_deployment_report(scans, scan_name):
    """Test that products reported as present are correct for the source.

    :id: d5d424bb-8183-4b60-b21a-1b4ed1d879c0
    :description: Test that products indicated as present are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that any products marked as present are expected to be found
           as is listed in the configuration file for the scan.
    :expectedresults: There are inspection results for each source we scanned
        and any products found are correctly identified.
    """
    all_matching_scans = scans.ok_with_expected_data_attr("products")
    finished_scan = all_matching_scans.get(scan_name)
    assert finished_scan, f"Scan {scan_name} must have encountered errors"
    assert finished_scan.report_id, f"No report id was returned from scan {scan_name}"
    report_content = finished_scan.deployments_report
    assert report_content.get("status") == "completed"
    system_fingerprints = report_content.get("system_fingerprints")
    found_hosts = {host.get("name"): host for host in system_fingerprints}
    if len(found_hosts) != len(system_fingerprints):
        msg = "Some discovered hosts have the same name. Test result might not be accurate."
        warnings.warn(msg)
    errors_found = []
    for hostname, expected_data in finished_scan.definition.expected_data.items():
        if not (expected_products := expected_data.products):
            continue
        if not found_hosts.get(hostname):
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_name}, but not found"
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


@pytest.mark.slow
@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", scan_names(has_distribution))
def test_OS_found_deployment_report(scans, scan_name):
    """Test that OS identified are correct for the source.

    :id: 0b16331c-2431-498a-9e84-65b3d66e4001
    :description: Test that OS type and version are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that the OS identified is expected to be found
           as is listed in the configuration file for the scan.
    :expectedresults: There are inspection results for each source we scanned
        and the operating system is correctly identified.
    """
    all_matching_scans = scans.ok_with_expected_data_attr("distribution")
    finished_scan = all_matching_scans.get(scan_name)
    assert finished_scan, f"Scan {scan_name} must have encountered errors"
    assert finished_scan.report_id, f"No report id was returned from scan {scan_name}"
    report_content = finished_scan.deployments_report
    assert report_content.get("status") == "completed"
    system_fingerprints = report_content.get("system_fingerprints")
    found_hosts = {}
    for host in system_fingerprints:
        found_hosts[host.get("name")] = host
    if len(found_hosts) != len(system_fingerprints):
        msg = "Some discovered hosts have the same name. Test result might not be accurate."
        warnings.warn(msg)

    errors_found = []
    for hostname, expected_data in finished_scan.definition.expected_data.items():
        expected_distribution = expected_data.distribution
        if not expected_distribution:
            continue

        actual_data = found_hosts.get(hostname, {})
        if not actual_data:
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_name}, but not found"
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
        found_is_redhat = actual_data.get("is_redhat", SENTINEL)

        if expected_distribution.release not in found_release:
            errors_found.append(
                "Expected OS release {0} for host {1} but " "found OS release {2}".format(
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
                "Expected OS named {0} for source {1} but " "found OS named {2}".format(
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
                "Expected OS version {0} for source {1} but " "found OS version {2}".format(
                    expected_distribution.version,
                    hostname,
                    found_version,
                )
            )

        if expected_distribution.is_redhat != found_is_redhat:
            errors_found.append(
                "Expected is_redhat to be {0} for source {1} but " "found {2}".format(
                    expected_distribution.is_redhat,
                    hostname,
                    found_is_redhat,
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


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", scan_names(has_installed_products))
def test_installed_products_deployment_report(scans, scan_name):
    """Test that installed products are correct for the source.

    :id: 5737d8bb-936f-4cdd-ab4b-20bedd9a6d48
    :description: Test that installed products are correctly identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that the installed products expected to be found,
           as listed in the configuration file for the scan, are present.
    :expectedresults: There are inspection results for each source we scanned
        and the installed products are correctly identified.
    """
    all_matching_scans = scans.ok_with_expected_data_attr("installed_products")
    finished_scan = all_matching_scans.get(scan_name)
    assert finished_scan, f"Scan {scan_name} must have encountered errors"
    assert finished_scan.report_id, f"No report id was returned from scan {scan_name}"
    report_content = finished_scan.deployments_report
    assert report_content.get("status") == "completed"
    system_fingerprints = report_content.get("system_fingerprints")
    found_hosts = {}
    for host in system_fingerprints:
        found_hosts[host.get("name")] = host
    if len(found_hosts) != len(system_fingerprints):
        msg = "Some discovered hosts have the same name. Test result might not be accurate."
        warnings.warn(msg)

    errors_found = []
    for hostname, expected_data in finished_scan.definition.expected_data.items():
        expected_installed_products = expected_data.installed_products
        if not expected_installed_products:
            continue

        actual_data = found_hosts.get(hostname, {})
        if not actual_data:
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_name}, but not found"
            )

        found_installed_products = actual_data.get("installed_products", [])
        found_installed_products = set(
            [product.get("id", "") for product in found_installed_products]
        )
        expected_installed_products = set(expected_installed_products)

        if expected_installed_products != found_installed_products:
            errors_found.append(
                "Host {0} expected installed products {1} but " "found {2}".format(
                    hostname,
                    expected_installed_products,
                    found_installed_products,
                )
            )

    assert len(errors_found) == 0, (
        "Installed product ids do not match!\n"
        "Differences are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(report_content),
        )
    )


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", scan_names(has_raw_facts))
def test_raw_facts_details_report(scans, scan_name):
    """Test that raw facts are correct for the source.

    :id: efca544f-d0f8-47ed-88a3-faace708b345
    :description: Test that raw facts are correctly identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that the found raw facts match these listed
           in the configuration file for the scan.
    :expectedresults: There are inspection results for each source we scanned
        and the raw facts are matching.
    """
    all_matching_scans = scans.ok_with_expected_data_attr("raw_facts")
    finished_scan = all_matching_scans.get(scan_name)
    assert finished_scan, f"Scan {scan_name} must have encountered errors"
    assert finished_scan.report_id, f"No report id was returned from scan {scan_name}"
    report_content = finished_scan.details_report
    found_hosts = {}
    for source in report_content.get("sources", []):
        source_type = source.get("source_type", "")

        hosthame_key = "uname_hostname"
        if source_type == "vcenter":
            hosthame_key = "vm.dns_name"
        elif source_type == "satellite":
            hosthame_key = "hostname"

        for host in source.get("facts", []):
            found_hosts[host.get(hosthame_key)] = host

    errors_found = []
    for hostname, expected_data in finished_scan.definition.expected_data.items():
        expected_raw_facts = expected_data.raw_facts
        if not expected_raw_facts:
            continue

        actual_data = found_hosts.get(hostname, {})
        if not actual_data:
            errors_found.append(
                f"Host '{hostname}' was expected for scan {scan_name}, but not found"
            )

        for raw_fact_name, raw_fact_value in expected_raw_facts.items():
            # None and False are valid raw values we might want to assert
            found_fact_value = actual_data.get(raw_fact_name, SENTINEL)
            if raw_fact_value != found_fact_value:
                errors_found.append(
                    "Host {0} expected fact {1} to have value {2} but " "found {3}".format(
                        hostname,
                        raw_fact_name,
                        raw_fact_value,
                        found_fact_value,
                    )
                )

    assert len(errors_found) == 0, (
        "Installed product ids do not match!\n"
        "Differences are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(report_content),
        )
    )


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_name", scan_names(has_aggregate))
def test_aggregate_report(scans, scan_name):
    """Test that aggregate values are correct for the source.

    :id: dd310642-75b3-47ca-a410-523f9f541ceb
    :description: Test that aggregate values are correctly tallied for the source.
    :steps:
        1) Request the aggregate json report for the scan.
        2) Assert that the found aggregate values match these listed
           in the configuration file for the scan.
    :expectedresults: There are inspection results for each source we scanned
        and the aggregate values are correctly tallied.
    """
    all_matching_scans = scans.ok_with_expected_data_attr("aggregate")
    finished_scan = all_matching_scans.get(scan_name)
    assert finished_scan, f"Scan {scan_name} must have encountered errors"
    assert finished_scan.report_id, f"No report id was returned from scan {scan_name}"
    aggregate_content = finished_scan.aggregate_report
    results = aggregate_content.get("results")
    diagnostics = aggregate_content.get("diagnostics")
    errors_found = []
    for hostname, expected_data in finished_scan.definition.expected_data.items():
        expected_aggregate = expected_data.aggregate
        if not expected_aggregate:
            continue
        for (
            expected_diagnostic_name,
            expected_diagnostic_value,
        ) in expected_aggregate.diagnostics.items():
            if diagnostics[expected_diagnostic_name] != expected_diagnostic_value:
                errors_found.append(
                    "Host {0} expected diagnostic for {1} to have value {2} but found {3}".format(
                        hostname,
                        expected_diagnostic_name,
                        expected_diagnostic_value,
                        diagnostics[expected_diagnostic_name],
                    )
                )
        for expected_result_name, expected_result_value in expected_aggregate.results.items():
            if results[expected_result_name] != expected_result_value:
                errors_found.append(
                    "Host {0} expected result for {1} to have value {2} but found {3}".format(
                        hostname,
                        expected_result_name,
                        expected_result_value,
                        results[expected_result_name],
                    )
                )
    assert len(errors_found) == 0, (
        "Aggregate report values do not match!\n"
        "Differences are listed below: \n {errors}.\n"
        "Full results for this scan were: {scan_results}".format(
            errors="\n\n======================================\n\n".join(errors_found),
            scan_results=pformat(aggregate_content),
        )
    )
