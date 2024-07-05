# coding=utf-8
"""Tests for qpc scan job commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import json
import random
import re

import pytest
from littletable import Table

from camayoc.constants import QPC_OPTIONAL_PRODUCTS
from camayoc.exceptions import NoMatchingDataDefinitionException
from camayoc.qpc_models import Scan
from camayoc.utils import uuid4

from .utils import report_detail
from .utils import scan_add_and_check
from .utils import scan_cancel
from .utils import scan_job
from .utils import scan_start
from .utils import wait_for_scan


@pytest.mark.runs_scan
def test_scanjob(data_provider, scans, qpc_server_config):
    """Scan a single source type.

    :id: 49ae6fef-ea41-4b91-b310-6054678bfbb4
    :description: Perform a scan on a single source type.
    :steps: Run a scan and download detils report using scan job id
        Run ``qpc scan start --sources <source>``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """

    def contains_single_source(sources_in_scan):
        return len(sources_in_scan) == 1

    scan = data_provider.scans.defined_one({"sources": contains_single_source})
    finished_scan = scans.with_name(scan.name)
    assert finished_scan.report_id, f"No report id was returned from scan {scan.name}"
    output_file = f"details-{uuid4()}.json"
    report = report_detail(
        {"json": None, "output-file": output_file, "scan-job": finished_scan.scan_job_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get("sources")


@pytest.mark.nightly_only
@pytest.mark.runs_scan
def test_scanjob_with_multiple_sources(qpc_server_config, data_provider):
    """Scan multiple source types.

    :id: 58fde39c-52d8-42ee-af4c-1d75a6dc80b0
    :description: Perform a scan on multiple source types.
    :steps: Run ``qpc scan start --sources <source1> <source2> ...``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """

    def has_two_sources(sources_in_scan):
        return len(sources_in_scan) >= 2

    try:
        scan = data_provider.scans.defined_one({"sources": has_two_sources})
    except NoMatchingDataDefinitionException:
        source_generator = data_provider.sources.defined_many({})
        source1 = next(source_generator)
        source2 = next(source_generator)
        scan = Scan(name=uuid4())
        scan_add_and_check(
            {
                "name": scan.name,
                "sources": f"{source1.name} {source2.name}",
            }
        )
        data_provider.mark_for_cleanup(scan)

    scan_name = scan.name
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    report_id = result["report_id"]
    assert report_id is not None
    output_file = "out.json"
    report = report_detail({"json": None, "output-file": output_file, "report": report_id})
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get("sources", []) != []


@pytest.mark.nightly_only
@pytest.mark.runs_scan
def test_scanjob_with_disabled_products(isolated_filesystem, qpc_server_config, data_provider):
    """Perform a scan with optional products disabled.

    :id: 3e01ea6c-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with optional products disabled and assert
        that report structure is valid.
    :steps:
        1) Add a scan using the
           camayoc.tests.qpc.cli.utils.scan_add_and_check function
        2) Start the scan and check that it has started
        3) When the scan job completes, access the Report
        4) Check that report structure is valid.
    :expectedresults: The scan must complete without any errors and a report
        should be available.
    """
    errors_found = []
    products_to_disable = random.sample(
        QPC_OPTIONAL_PRODUCTS, k=random.randint(1, len(QPC_OPTIONAL_PRODUCTS))
    )
    scan_name = uuid4()
    source = data_provider.sources.new_one({"type": "network"}, data_only=False)
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source.name,
            "disabled-optional-products": " ".join(products_to_disable),
        }
    )
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    report_id = result["report_id"]
    assert report_id is not None
    output_file = "out.json"
    report = report_detail({"json": None, "output-file": output_file, "report": report_id})
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get("sources")
        if not sources:
            errors_found.append("Report does not include sources.")
        for source in sources:
            facts = source.get("facts")
            if not facts:
                errors_found.append(
                    "Report does not include facts key for source {source}.".format(
                        source=source.get("source_name")
                    )
                )

    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@pytest.mark.nightly_only
@pytest.mark.runs_scan
def test_scanjob_with_enabled_extended_products(qpc_server_config, data_provider):
    """Perform a scan with extended products enabled.

    :id: 2294649e-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with extended products enabled and
        assert that report structure is valid.
    :steps:
        1) Add a scan using the
           camayoc.tests.qpc.cli.utils.scan_add_and_check function
        2) Start the scan and check that it has started
        3) When the scan job completes, access the Report
        4) Check that report structure is valid.
    :expectedresults: The scan must complete without any errors and a report
        should be available.
    """
    errors_found = []
    products_to_extended_search = random.sample(
        QPC_OPTIONAL_PRODUCTS, k=random.randint(1, len(QPC_OPTIONAL_PRODUCTS))
    )
    scan_name = uuid4()
    source = data_provider.sources.new_one({"type": "network"}, data_only=False)
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source.name,
            "enabled-ext-product-search": " ".join(products_to_extended_search),
        }
    )
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    report_id = result["report_id"]
    assert report_id is not None
    output_file = "out.json"
    report = report_detail({"json": None, "output-file": output_file, "report": report_id})
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get("sources")
        if not sources:
            errors_found.append("Report does not include sources.")
        for source in sources:
            facts = source.get("facts")
            if not facts:
                errors_found.append(
                    "Report does not include facts key for source {source}.".format(
                        source=source.get("source_name")
                    )
                )

    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@pytest.mark.runs_scan
def test_scanjob_cancel(qpc_server_config, data_provider):
    """Perform a scan and ensure it can be canceled.

    :id: b5c11b82-e86e-478b-b885-89a577f81b13
    :description: Start a scan, then cancel it.
    :steps:
        1) Run ``qpc scan start --sources <source>`` and store its ID.
        2) Cancel the scan by running ``qpc scan cancel --id <id>``
    :expectedresults: The scan must be canceled.
    """
    # There's nothing fundamentally wrong with other source types.
    # In our environment, they tend to finish too quickly, largely
    # increasing a risk of test failing because job finished before
    # we checked if it started.
    source = data_provider.sources.new_one({"type": Table.eq("network")}, data_only=False)
    scan_name = uuid4()
    scan_add_and_check({"name": scan_name, "sources": source.name})
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status="running", timeout=60)
    scan_cancel({"id": scan_job_id})
    wait_for_scan(scan_job_id, status="canceled", timeout=60)
