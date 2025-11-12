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
import tarfile

import pytest
from littletable import Table

from camayoc.config import settings
from camayoc.constants import QPC_OPTIONAL_PRODUCTS
from camayoc.constants import SOURCE_TYPES_WITH_LIGHTSPEED_SUPPORT
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.utils import assert_ansible_logs
from camayoc.tests.qpc.utils import assert_lightspeed_report
from camayoc.tests.qpc.utils import assert_sha256sums
from camayoc.utils import uuid4

from .utils import report_detail
from .utils import report_download
from .utils import scan_add_and_check
from .utils import scan_cancel
from .utils import scan_job
from .utils import scan_start
from .utils import scans_with_source_type
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
@pytest.mark.slow
@pytest.mark.runs_scan
def test_scanjob_with_multiple_sources(qpc_server_config, data_provider):
    """Scan multiple source types.

    :id: 58fde39c-52d8-42ee-af4c-1d75a6dc80b0
    :description: Perform a scan on multiple source types.
    :steps: Run ``qpc scan start --sources <source1> <source2> ...``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    source_generator = data_provider.sources.defined_many(
        {"type": Table.is_in(("network", "satellite", "vcenter"))}
    )
    sources = [next(source_generator)]
    while True:
        new_source = next(source_generator)
        if new_source.source_type == sources[0].source_type:
            continue
        sources.append(new_source)
        break

    scan = Scan(name=uuid4())
    scan_name = scan.name
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": " ".join(s.name for s in sources),
        }
    )
    data_provider.mark_for_cleanup(scan)

    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id)
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
@pytest.mark.slow
@pytest.mark.runs_scan
def test_scanjob_with_all_sources(qpc_server_config, data_provider):
    """Scan with all known source types.

    :id: 6fde0327-5553-41b8-8c90-1acf7258dec3
    :description: Perform a scan on all known source types.
    :steps: Run ``qpc scan start --sources <source1> <source2> ...``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    source_generator = data_provider.sources.defined_many({})
    sources = []
    for new_source in source_generator:
        known_source_types = [source.source_type for source in sources]
        if new_source.source_type in known_source_types:
            continue
        sources.append(new_source)

    scan = Scan(name=uuid4())
    scan_name = scan.name
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": " ".join(s.name for s in sources),
        }
    )
    data_provider.mark_for_cleanup(scan)

    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id)
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
@pytest.mark.slow
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
    wait_for_scan(scan_job_id)
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
@pytest.mark.slow
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
    wait_for_scan(scan_job_id)
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


@pytest.mark.upgrade_only
@pytest.mark.runs_scan
@pytest.mark.skipif(
    bool(settings.camayoc.snapshot_test_reference_synthetic),
    reason="Snapshot reference data is synthetic, scans on rerun would fail",
)
def test_rerun_scanjob(tmp_path, qpc_server_config, source_type):
    """After upgrade, run existing scan again.

    :id: 283c89be-b950-481d-ad81-76b74663823e
    :description: Find a scan that was run before the upgrade and run it again.
    :steps:
        1) Select a random scan that used a source of given type.
        2) Run that scan again
        3) Wait for scan to complete.
        4) Download scan report.
    :expectedresults: Scan is completed, report is downloaded.
    """
    matching_scans = scans_with_source_type(source_type)
    if not matching_scans:
        pytest.skip("There are no scans with sources of this type")

    scan = random.choice(matching_scans)

    result = scan_start({"name": scan.get("name")})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    assert result["report_id"]

    is_network_scan = any(source.get("source_type") == "network" for source in scan.get("sources"))
    scan_source_types = {source.get("source_type") for source in scan.get("sources")}
    expect_lightspeed_report = bool(
        scan_source_types.intersection(set(SOURCE_TYPES_WITH_LIGHTSPEED_SUPPORT))
    )
    downloaded_report = tmp_path / "report.tar.gz"

    report_download({"scan-job": scan_job_id, "output-file": downloaded_report.as_posix()})

    tarfile.open(downloaded_report).extractall(tmp_path, filter="tar")
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)
    assert_lightspeed_report(tmp_path, expect_lightspeed_report)
