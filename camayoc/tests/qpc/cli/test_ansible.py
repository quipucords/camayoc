"""Tests for Ansible Automation Platform (ansible) sources.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import re
from uuid import uuid4

import pytest

from camayoc.config import settings
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import wait_for_scan
from camayoc.types.settings import SourceOptions

from .utils import retrieve_report
from .utils import scan_add_and_check


def ansible_sources():
    for source_definition in settings.sources:
        if source_definition.type != "ansible":
            continue
        yield pytest.param(source_definition, id=source_definition.name)


def _run_ansible_scan(data_provider, source_definition: SourceOptions):
    source = data_provider.sources.new_one({"name": source_definition.name}, data_only=False)
    scan_name = uuid4()
    scan_add_and_check({"name": scan_name, "sources": source.name})
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    output = scan_start({"name": scan_name})
    match_scan_id = re.match(r'Scan "(\d+)" started.', output)
    assert match_scan_id is not None
    scan_job_id = match_scan_id.group(1)
    wait_for_scan(scan_job_id)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    details, deployments, aggregate = retrieve_report(scan_job_id)
    return source, details, deployments, aggregate


def validate_ansible_report_minimum(source_name, details, deployments, aggregate):
    """Validate minimal ansible report attributes (empty inventory is OK).

    :id: 3f8c2a71-6d4e-4b9a-9e2f-1a7c5d8b0e44
    """
    assert details is not None, "details report missing from download"
    assert deployments is not None, "deployments report missing from download"
    assert aggregate is not None, "aggregate report missing from download"

    ansible_sources_in_report = [
        report_source
        for report_source in details.get("sources", [])
        if report_source.get("source_type") == "ansible"
    ]
    assert len(ansible_sources_in_report) == 1
    report_source = ansible_sources_in_report[0]
    assert report_source.get("source_name") == source_name

    facts = report_source.get("facts", [])
    assert len(facts) == 1
    fact = facts[0]
    assert "instance_details" in fact
    assert "hosts" in fact

    instance_details = fact["instance_details"]
    system_name = instance_details.get("system_name")
    version = instance_details.get("version")
    assert isinstance(system_name, str) and system_name
    assert isinstance(version, str) and version

    hosts = fact["hosts"]
    assert isinstance(hosts, list)
    host_count = len(hosts)

    ansible_fingerprints = [
        fingerprint
        for fingerprint in deployments.get("system_fingerprints", [])
        if fingerprint.get("name") == system_name
        and any(source.get("source_type") == "ansible" for source in fingerprint.get("sources", []))
    ]
    assert len(ansible_fingerprints) >= 1
    assert ansible_fingerprints[0].get("os_version") == version

    results = aggregate.get("results", {})
    assert results.get("ansible_hosts_in_database") == host_count


def validate_ansible_unique_hosts_collected(source_name, details, deployments, aggregate):
    """Validate unique-hosts collection succeeded (host_metrics or /jobs/ fallback)."""
    validate_ansible_report_minimum(source_name, details, deployments, aggregate)

    report_source = next(
        report_source
        for report_source in details.get("sources", [])
        if report_source.get("source_type") == "ansible"
    )
    facts = report_source.get("facts", [])
    assert len(facts) == 1
    fact = facts[0]
    missing = [key for key in ("jobs", "comparison") if key not in fact]
    assert not missing, f"Details facts missing required keys: {missing}"

    hosts = fact["hosts"]
    host_count = len(hosts)
    jobs = fact["jobs"]
    assert isinstance(jobs.get("unique_hosts"), list)
    assert isinstance(jobs.get("job_ids"), list)

    comparison = fact["comparison"]
    assert comparison.get("number_of_hosts_in_inventory") == host_count
    assert comparison.get("number_of_hosts_only_in_jobs") == len(
        comparison.get("hosts_only_in_jobs", [])
    )
    assert set(comparison.get("hosts_in_inventory", [])) == {host.get("name") for host in hosts}

    results = aggregate.get("results", {})
    diagnostics = aggregate.get("diagnostics", {})
    assert results.get("ansible_hosts_in_jobs") == len(set(jobs["unique_hosts"]))
    assert results.get("ansible_hosts_all") == len(
        set(comparison.get("hosts_in_inventory", []))
        | set(comparison.get("hosts_only_in_jobs", []))
    )
    assert diagnostics.get("inspect_result_status_success") == 1
    assert diagnostics.get("inspect_result_status_failed") == 0


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_definition", ansible_sources())
def test_ansible_unique_hosts_collected(
    qpc_server_config, data_provider, source_definition: SourceOptions
):
    """Scan an ansible source and validate unique-hosts collection end-to-end.

    :id: 9b1e4d52-8c70-4f1a-a3d6-5e2f7c8a9012
    :description: Perform an ansible / AAP scan and ensure unique-hosts facts
        (``jobs`` and ``comparison``) are present with a successful inspect
        status. This covers the host_metrics 40x fallback to ``/jobs/``: when
        host_metrics is advertised but returns 401/403/404, Discovery should
        still collect unique hosts via jobs instead of failing inspect. Also
        validates minimal report attributes (details, deployments, aggregate).
    :steps:
        1. Add source with credential for an AAP / Ansible Controller
        2. Perform a scan
        3. Collect the report
    :expectedresults: Scan finishes with successful inspect diagnostics;
        details include jobs and comparison; aggregate host metrics are
        internally consistent. Empty unique_hosts / job_ids are allowed.
        Controller fingerprint matches instance_details, and aggregate
        inventory count matches ``len(hosts)`` (including zero).
    """
    source, details, deployments, aggregate = _run_ansible_scan(data_provider, source_definition)
    validate_ansible_unique_hosts_collected(source.name, details, deployments, aggregate)
