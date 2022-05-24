# coding=utf-8
"""Tests for qpc scan job commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import json
import pytest
import re

from camayoc.constants import (
    QPC_BRMS_EXTENDED_FACTS,
    QPC_BRMS_RAW_FACTS,
    QPC_EAP_EXTENDED_FACTS,
    QPC_EAP_RAW_FACTS,
    QPC_FUSE_EXTENDED_FACTS,
    QPC_FUSE_RAW_FACTS,
    QPC_OPTIONAL_PRODUCTS,
)
from camayoc.tests.qpc.utils import mark_runs_scans
from camayoc.utils import uuid4

from .utils import (
    config_sources,
    report_detail,
    scan_add_and_check,
    scan_cancel,
    scan_job,
    scan_pause,
    scan_restart,
    scan_start,
    wait_for_scan,
)


@mark_runs_scans
@pytest.mark.troubleshoot
def test_scanjob(isolated_filesystem, qpc_server_config, scan):
    """Scan a single source type.

    :id: 49ae6fef-ea41-4b91-b310-6054678bfbb4
    :description: Perform a scan on a single source type.
    :steps: Run ``qpc scan start --sources <source>``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    scan_add_and_check({"name": scan["name"], "sources": " ".join(scan["sources"])})

    result = scan_start({"name": scan["name"]})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1800)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    report_id = result["report_id"]
    assert report_id is not None
    output_file = "out.json"
    report = report_detail(
        {"json": None, "output-file": output_file, "report": report_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get("sources", []) != []


@mark_runs_scans
def test_scanjob_with_multiple_sources(isolated_filesystem, qpc_server_config):
    """Scan multiple source types.

    :id: 58fde39c-52d8-42ee-af4c-1d75a6dc80b0
    :description: Perform a scan on multiple source types.
    :steps: Run ``qpc scan start --sources <source1> <source2> ...``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    scan_name = uuid4()
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": " ".join([source["name"] for source in config_sources()]),
        }
    )
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
    report = report_detail(
        {"json": None, "output-file": output_file, "report": report_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get("sources", []) != []


@pytest.mark.skip(reason="Skipped until Quipucords Issue #2038 us resolved")
@mark_runs_scans
def test_scanjob_with_disabled_products(isolated_filesystem, qpc_server_config):
    """Perform a scan with optional products disabled.

    :id: 3e01ea6c-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with optional products disabled and assert
        that the product facts are not collected in the report.
    :steps:
        1) Add a scan using the
           camayoc.tests.qpc.cli.utils.scan_add_and_check function
        2) Start the scan and check that it has started
        3) When the scan job completes, access the Report
        4) Check that the disabled facts are not present in the facts
           section of the report
    :expectedresults: The scan must completed without any error and a report
        should be available. The disabled products should not have results in
        the report.
    """
    errors_found = []
    disabled_facts = QPC_EAP_RAW_FACTS + QPC_BRMS_RAW_FACTS + QPC_FUSE_RAW_FACTS
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "disabled-optional-products": " ".join(QPC_OPTIONAL_PRODUCTS),
        }
    )
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
    report = report_detail(
        {"json": None, "output-file": output_file, "report": report_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get("sources")
        if sources:
            for source in sources:
                facts = source.get("facts")
                for fact in disabled_facts:
                    for dictionary in facts:
                        if fact in dictionary.keys():
                            errors_found.append(
                                "The fact {fact} should have "
                                "been DISABLED but was found "
                                "in report.".format(fact=fact)
                            )

    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@mark_runs_scans
def test_scanjob_with_enabled_extended_products(isolated_filesystem, qpc_server_config):
    """Perform a scan with extended products enabled.

    :id: 2294649e-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with extended products enabled and
        assert that the extended facts are collected in the report.
    :steps:
        1) Add a scan using the
           camayoc.tests.qpc.cli.utils.scan_add_and_check function
        2) Start the scan and check that it has started
        3) When the scan job completes, access the Report
        4) Check that the extended facts are present in the facts
           section of the report
    :expectedresults: The scan must completed without any error and a report
        should be available. The extended products should have results in
        the report.
    """
    errors_found = []
    extended_facts = (
        QPC_EAP_EXTENDED_FACTS + QPC_BRMS_EXTENDED_FACTS + QPC_FUSE_EXTENDED_FACTS
    )
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "enabled-ext-product-search": "jboss_fuse jboss_brms jboss_eap",
        }
    )
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
    report = report_detail(
        {"json": None, "output-file": output_file, "report": report_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get("sources")
        if sources:
            for source in sources:
                facts = source.get("facts")
                for fact in extended_facts:
                    for dictionary in facts:
                        if fact not in dictionary.keys():
                            errors_found.append(
                                "The fact {fact} should have "
                                "been ENABLED but was not found "
                                "in report.".format(fact=fact)
                            )

    assert len(errors_found) == 0, "\n================\n".join(errors_found)


@pytest.mark.skip(reason="Skipping until Quipucords Issue #2040 resoloved")
@mark_runs_scans
def test_scanjob_restart(isolated_filesystem, qpc_server_config):
    """Perform a scan and ensure it can be paused and restarted.

    :id: 7eb79aa8-fe3d-4fcd-9f1a-5e2d4df2f3b6
    :description: Start a scan, then pause it and finally restart it.
    :steps:
        1) Run ``qpc scan start --sources <source>`` and store its ID.
        2) Stop the scan by running ``qpc scan stop --id <id>``
        3) Restart the scan by running ``qpc scan restart --id <id>``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    scan_name = uuid4()
    scan_add_and_check({"name": scan_name, "sources": config_sources()[0]["name"]})
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status="running", timeout=60)
    scan_pause({"id": scan_job_id})
    wait_for_scan(scan_job_id, status="paused", timeout=60)
    scan_restart({"id": scan_job_id})
    wait_for_scan(scan_job_id)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    report_id = result["report_id"]
    assert report_id is not None
    output_file = "out.json"
    report = report_detail(
        {"json": None, "output-file": output_file, "report": report_id}
    )
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get("sources", []) != []


@mark_runs_scans
def test_scanjob_cancel(isolated_filesystem, qpc_server_config):
    """Perform a scan and ensure it can be canceled.

    :id: b5c11b82-e86e-478b-b885-89a577f81b13
    :description: Start a scan, then cancel it and finally check it can't be
        restarted.
    :steps:
        1) Run ``qpc scan start --sources <source>`` and store its ID.
        2) Cancel the scan by running ``qpc scan cancel --id <id>``
        3) Try to restart the scan by running ``qpc scan restart --id <id>``
    :expectedresults: The scan must be canceled and can't not be restarted.
    """
    scan_name = uuid4()
    scan_add_and_check({"name": scan_name, "sources": config_sources()[0]["name"]})
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status="running", timeout=60)
    scan_cancel({"id": scan_job_id})
    wait_for_scan(scan_job_id, status="canceled", timeout=60)
    result = scan_restart({"id": scan_job_id}, exitstatus=1)
    assert result.startswith(
        "Error: Scan cannot be restarted. The scan must be paused for it to "
        "be restarted."
    )


@pytest.mark.skip(reason="Skipping until Quipucords Issue #2040 resoloved")
@mark_runs_scans
def test_scanjob_cancel_paused(isolated_filesystem, qpc_server_config):
    """Perform a scan and ensure it can be canceled even when paused.

    :id: 62943ef9-8989-4998-8456-8073f8fd9ce4
    :description: Start a scan, next stop it, then cancel it and finally check
        it can't be restarted.
    :steps:
        1) Run ``qpc scan start --sources <source>`` and store its ID.
        2) Pause the scan by running ``qpc scan pause --id <id>``
        3) Cancel the scan by running ``qpc scan cancel --id <id>``
        4) Try to restart the scan by running ``qpc scan restart --id <id>``
    :expectedresults: The scan must be canceled and can't not be restarted.
    """
    scan_name = uuid4()
    scan_add_and_check({"name": scan_name, "sources": config_sources()[0]["name"]})
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status="running", timeout=60)
    scan_pause({"id": scan_job_id})
    wait_for_scan(scan_job_id, status="paused", timeout=60)
    scan_cancel({"id": scan_job_id})
    wait_for_scan(scan_job_id, status="canceled", timeout=60)
    result = scan_restart({"id": scan_job_id}, exitstatus=1)
    assert result.startswith(
        "Error: Scan cannot be restarted. The scan must be paused for it to "
        "be restarted."
    )
