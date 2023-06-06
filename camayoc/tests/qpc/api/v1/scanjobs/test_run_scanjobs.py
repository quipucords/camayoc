# coding=utf-8
"""Tests for quipucords scanjobs.

These tests are parametrized on the inventory listed in the config file.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
import random
from pprint import pformat

import pytest

from camayoc import utils
from camayoc.constants import QPC_OPTIONAL_PRODUCTS
from camayoc.qpc_models import Scan
from camayoc.qpc_models import ScanJob
from camayoc.tests.qpc.api.v1.conftest import scan_list
from camayoc.tests.qpc.api.v1.utils import wait_until_state
from camayoc.types.settings import ScanOptions


@pytest.mark.skip(reason="Test is flaky. Skipping until Quipucords Issue #2040 resoloved")
@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_scan_complete(scan_info: ScanOptions):
    """Test that each scan completed without failures.

    :id: 4e7a608e-a18d-48db-b263-a0d5474385dd
    :description: Test if the scan completed.
    :steps: Check the final status of the scan.
    :expectedresults: Scans should complete and report their finished status.
    """

    def get_scan_result(scan_name):
        return {}

    result = get_scan_result(scan_info.name)
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


@pytest.mark.runs_scan
@pytest.mark.parametrize("scan_info", scan_list(), ids=utils.name_getter)
def test_scan_task_results(data_provider, scan_info: ScanOptions):
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
    scan = data_provider.scans.defined_one({"name": scan_info.name})
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, state="stopped")
    assertion_error_message = "Details of failed scan : {0}".format(pformat(scanjob.read().json()))

    task_results = scanjob.read().json().get("tasks")
    scan_data = scanjob.read().json()

    # assert count is correct for entire scan
    sys_count = scan_data.get("systems_count", 0)
    num_failed = scan_data.get("systems_failed", 0)
    num_scanned = scan_data.get("systems_scanned", 0)
    num_unreachable = scan_data.get("systems_unreachable", 0)
    assert num_scanned == (sys_count - num_failed - num_unreachable), assertion_error_message

    if not task_results:
        pytest.xfail(
            reason="No task results were returned "
            "from scan named {scan_name}".format(scan_name=scan_info.name)
        )

    for task in task_results:
        # assert count is correct for each connect and inspect task
        sys_count = task.get("systems_count", 0)
        num_failed = task.get("systems_failed", 0)
        num_scanned = task.get("systems_scanned", 0)
        num_unreachable = task.get("systems_unreachable", 0)
        assert num_scanned == (sys_count - num_failed - num_unreachable), assertion_error_message


@pytest.mark.runs_scan
def test_disabled_optional_products(data_provider):
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
    products_to_disable = random.sample(
        QPC_OPTIONAL_PRODUCTS, k=random.randint(1, len(QPC_OPTIONAL_PRODUCTS))
    )
    disabled_optional_products = {name: True for name in products_to_disable}

    source = data_provider.sources.new_one({"type": "network"}, data_only=False)
    scan = Scan(source_ids=[source._id], disabled_optional_products=disabled_optional_products)
    scan.create()
    data_provider.mark_for_cleanup(scan)
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, state="stopped")

    errors_found = []
    # grab disabled products from results
    returned_optional_products = (
        scanjob.read().json().get("options").get("disabled_optional_products")
    )
    for product in disabled_optional_products.keys():
        if disabled_optional_products[product] != returned_optional_products[product]:
            errors_found.append(
                "The product {product_name} should have been set to "
                "{product_status} but was returned with a value of "
                "{returned_status} on scan named {scan_name}".format(
                    product_name=product,
                    product_status=disabled_optional_products[product],
                    returned_status=returned_optional_products[product],
                    scan_name=scan.name,
                )
            )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@pytest.mark.runs_scan
def test_enabled_extended_product_search(data_provider):
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
    products_to_enable_extended_search = random.sample(
        QPC_OPTIONAL_PRODUCTS, k=random.randint(1, len(QPC_OPTIONAL_PRODUCTS))
    )
    enabled_extended_products = {name: True for name in products_to_enable_extended_search}

    source = data_provider.sources.new_one({"type": "network"}, data_only=False)
    scan = Scan(source_ids=[source._id], enabled_extended_product_search=enabled_extended_products)
    scan.create()
    data_provider.mark_for_cleanup(scan)
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, state="stopped")

    errors_found = []
    # grab extended products from config file
    # grab extended products from results
    returned_extended_products = (
        scanjob.read().json().get("options").get("enabled_extended_product_search")
    )
    for product in enabled_extended_products:
        if enabled_extended_products[product] != returned_extended_products[product]:
            errors_found.append(
                "The product {product_name} should have been set to "
                "{product_status} but was returned with a value of "
                "{returned_status} on scan named {scan_name}".format(
                    product_name=product,
                    product_status=enabled_extended_products[product],
                    returned_status=returned_extended_products[product],
                    scan_name=scan.name,
                )
            )
    assert len(errors_found) == 0, "\n================\n".join(errors_found)
