# coding=utf-8
"""Tests for quipucords scanjobs.

These tests are parametrized on the inventory listed in the config file.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: quipucords
:testtype: functional
:upstream: yes
"""
from pprint import pformat

import pytest

from camayoc import utils
from camayoc.constants import QPC_BRMS_EXTENDED_FACTS
from camayoc.constants import QPC_BRMS_RAW_FACTS
from camayoc.constants import QPC_EAP_EXTENDED_FACTS
from camayoc.constants import QPC_EAP_RAW_FACTS
from camayoc.constants import QPC_FUSE_EXTENDED_FACTS
from camayoc.constants import QPC_FUSE_RAW_FACTS
from camayoc.tests.qpc.api.v1.conftest import get_scan_result
from camayoc.tests.qpc.api.v1.conftest import scan_list
from camayoc.tests.qpc.utils import mark_runs_scans


@pytest.mark.skip(reason="Test is flaky. Skipping until Quipucords Issue #2040 resoloved")
@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_scan_complete(scan_info):
    """Test that each scan completed without failures.

    :id: 4e7a608e-a18d-48db-b263-a0d5474385dd
    :description: Test if the scan completed.
    :steps: Check the final status of the scan.
    :expectedresults: Scans should complete and report their finished status.
    """
    result = get_scan_result(scan_info["name"])
    if result["final_status"] != "completed":
        raise AssertionError(
            "Scan did not complete. Its final status was {status}.\n"
            " NOTE: A scan will be reported as failed if there were\n"
            " unreachable hosts.\n"
            " ============================================================\n"
            " Any additional HTTP errors encountered while attempting\n"
            " to run the scan are listed here: \n"
            "{errors}\n"
            " ============================================================\n"
            " Details from the scan including scan_id, scan_job_id, and the\n"
            "inspeciton results:\n"
            "{results}\n".format(
                status=result["final_status"],
                errors="\n".join(result["errors"]),
                results=pformat(result),
            )
        )


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_scan_task_results(scan_info):
    """Test the scan task results of each scan.

    :id: 8087fdc9-6626-476a-a11a-4783cbf501a0
    :description: Test the connection results of the scan
    :steps:
        1) Iterate over sources that we have connection results for.
        2) Inspect server arithmetic regarding number of systems scanned
    :expectedresults: There are task results for each source we scanned
       and we get an accurate count of how many were reached and how many
       failed for all tasks.
    """
    result = get_scan_result(scan_info["name"])
    assertion_error_message = "Details of failed scan : {0}".format(pformat(result))
    task_results = result.get("task_results")
    scan = result.get("scan_results")

    # assert count is correct for entire scan
    sys_count = scan.get("systems_count", 0)
    num_failed = scan.get("systems_failed", 0)
    num_scanned = scan.get("systems_scanned", 0)
    num_unreachable = scan.get("systems_unreachable", 0)
    assert num_scanned == (sys_count - num_failed - num_unreachable), assertion_error_message

    if not task_results:
        pytest.xfail(
            reason="No task results were returned "
            "from scan named {scan_name}".format(scan_name=scan_info["name"])
        )

    for task in task_results:
        # assert count is correct for each connect and inspect task
        sys_count = task.get("systems_count", 0)
        num_failed = task.get("systems_failed", 0)
        num_scanned = task.get("systems_scanned", 0)
        num_unreachable = task.get("systems_unreachable", 0)
        assert num_scanned == (sys_count - num_failed - num_unreachable), assertion_error_message


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_disabled_optional_products_facts(scan_info):
    """Test scan jobs from scans with disabled optional products.

    :id: 6f91ea5c-32b9-11e8-b467-0ed5f89f718b
    :description: Test that scan jobs of scans with disabled products
        are not gathering the raw_facts defined in the roles of the
        disabled products.
    :steps:
        1) Iterate over the scans and gather the disabled_optional_products
        2) For any scan that was defined with disabled_optional_products:
            a) Create a facts_to_ignore list composed of raw_facts for each
                disabled role
            b) Iterate through the inspection results fact dictionaries
            c) Assert that no facts that should be ignored are in the
                dictionaries
    :expectedresults: No facts are collected for disabled products
    """
    errors_found = []
    scan = get_scan_result(scan_info["name"])
    facts_to_ignore = []
    disabled_optional_products = scan_info.get("disabled_optional_products")
    if disabled_optional_products:
        # Build the list of facts that should not be in inspection results
        for product in disabled_optional_products.keys():
            if product == "jboss_eap":
                facts_to_ignore += QPC_EAP_RAW_FACTS
            elif product == "jboss_fuse":
                facts_to_ignore += QPC_FUSE_RAW_FACTS
            elif product == "jboss_brms":
                facts_to_ignore += QPC_BRMS_RAW_FACTS
        # grab the inspection results of the scan
        inspection_results = scan.get("inspection_results")
        if not inspection_results:
            pytest.xfail(
                reason="No inspection results were returned "
                "from scan named {scan_name}".format(scan_name=scan_info["name"])
            )
        for system in inspection_results:
            fact_dicts = system.get("facts")
            # grab the facts for each system
            for dictionary in fact_dicts:
                for fact in facts_to_ignore:
                    if fact in dictionary.values():
                        errors_found.append(
                            "Found fact {fact_name} that should have been "
                            "DISABLED on scan named {scan_name}".format(
                                fact_name=fact, scan_name=scan_info["name"]
                            )
                        )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_disabled_optional_products(scan_info):
    """Test scan jobs from scans with disabled_optional_products.

    :id: 77aa1f0c-32be-11e8-b467-0ed5f89f718b
    :description: Test that scans created with disabled products
        retain the same disabled products when results are obtained
        from the api
    :steps: 1) Iterate over scans and gather disabled products
            2) If the scans have disabled products, grab the
                disabled_products that were returned in the scan results
            3) Check that each specified product has the same value
                after being returned from the api
    :expectedresults: The values for disabled products specified in the
        config file are the same as those returned from the api
    """
    scan = get_scan_result(scan_info["name"])
    errors_found = []
    # grab disabled products from config file
    specified_optional_products = scan_info.get("disabled_optional_products")
    if specified_optional_products:
        # grab disabled products from results
        returned_optional_products = (
            scan.get("scan_results").get("options").get("disabled_optional_products")
        )
        for product in specified_optional_products:
            if specified_optional_products[product] != returned_optional_products[product]:
                errors_found.append(
                    "The product {product_name} should have been set to "
                    "{product_status} but was returned with a value of "
                    "{returned_status} on scan named {scan_name}".format(
                        product_name=product,
                        product_status=specified_optional_products[product],
                        returned_status=returned_optional_products[product],
                        scan_name=scan_info["name"],
                    )
                )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_enabled_extended_product_search_facts(scan_info):
    """Test scan jobs from scans with enabled extended products search.

    :id: 2815ca08-376f-11e8-b467-0ed5f89f718b
    :description: Test that scan jobs of scans with enabled extended
        products are gathering the raw_facts defined in the roles of the
        extended products.
    :steps:
        1) Iterate over the scans and gather the enabled products
        2) For any scan that was defined with enabled products:
            a) Create a facts_to_include list composed of raw_facts for
                each enabled task
            b) Grab the inspection results if they exist, xfail if not
            c) Iterate through the inspection results fact dictionaries
            d) Assert that facts that should be gathered are included in
                the inspection results
    :expectedresults: Facts are collected for enabled extended products
    """
    errors_found = []
    scan = get_scan_result(scan_info["name"])
    facts_to_include = []
    enabled_extended_products = scan_info.get("enabled_extended_product_search")
    if enabled_extended_products:
        # Build the list of extended facts that should be collected
        for product in enabled_extended_products.keys():
            if product == "jboss_eap":
                facts_to_include += QPC_EAP_EXTENDED_FACTS
            elif product == "jboss_fuse":
                facts_to_include += QPC_FUSE_EXTENDED_FACTS
            elif product == "jboss_brms":
                facts_to_include += QPC_BRMS_EXTENDED_FACTS
        # grab the inspection results of the scan
        inspection_results = scan.get("inspection_results")
        if not inspection_results:
            pytest.xfail(
                reason="No inspection results were returned from "
                "scan named {scan_name}".format(scan_name=scan_info["name"])
            )
        for system in inspection_results:
            facts_not_found = []
            # grab the facts for each system
            fact_dicts = system.get("facts")
            for fact in facts_to_include:
                fact_found = False
                for dictionary in fact_dicts:
                    if fact in dictionary.values():
                        fact_found = True
                if not fact_found:
                    facts_not_found.append(fact)
            if len(facts_not_found) != 0:
                errors_found.append(
                    "The facts {facts} should have been ENABLED on "
                    "the scan named {scan_name} but were not found: "
                    "on the system {system_name}.".format(
                        facts=facts_not_found,
                        scan_name=scan_info["name"],
                        system_name=system.get("name"),
                    )
                )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_enabled_extended_product_search(scan_info):
    """Test scan jobs from scans with enabled extended product search.

    :id: 597235de-376d-11e8-b467-0ed5f89f718b
    :description: Test that scans created with enabled extended product
        search retain the same enabled products when results are obtained
        from the api
    :steps: 1) Iterate over scans and gather enabled products
            2) If the scans have enabled products, grab the
                enabled_products that were returned in the scan results
            3) Check that each specified product has the same value
                after being returned from the api
    :expectedresults: The values for extended products specified in the
        config file are the same as those returned from the api
    """
    scan = get_scan_result(scan_info["name"])
    errors_found = []
    # grab extended products from config file
    specified_extended_products = scan_info.get("enabled_extended_product_search")
    if specified_extended_products:
        # grab extended products from results
        returned_extended_products = (
            scan.get("scan_results").get("options").get("enabled_extended_product_search")
        )
        for product in specified_extended_products:
            if specified_extended_products[product] != returned_extended_products[product]:
                errors_found.append(
                    "The product {product_name} should have been set to "
                    "{product_status} but was returned with a value of "
                    "{returned_status} on scan named {scan_name}".format(
                        product_name=product,
                        product_status=specified_extended_products[product],
                        returned_status=returned_extended_products[product],
                        scan_name=scan_info["name"],
                    )
                )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)
