"""Tests for OpenShift sources.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
import json
import pathlib
import re
import tarfile

import pytest

from camayoc import utils
from camayoc.constants import AUTH_TOKEN_INPUT
from camayoc.tests.qpc.cli.utils import config_openshift
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import report_download
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import source_add_and_check
from camayoc.tests.qpc.cli.utils import wait_for_scan


def retrieve_report(scan_name, scan_job_id):
    output_file = f"report-{scan_name}.tar.gz"
    report_download({"scan-job": scan_job_id, "output-file": output_file})
    details = deployments = None
    with tarfile.open(output_file) as pkg:
        for member in pkg.getmembers():
            if member.name.endswith("details.json"):
                data = pkg.extractfile(member).read()
                details = json.loads(data)
            if member.name.endswith("deployments.json"):
                data = pkg.extractfile(member).read()
                deployments = json.loads(data)
    pathlib.Path.unlink(output_file)
    return details, deployments


def validate_openshift_report(cluster, details, deployments):
    assert details["sources"]
    assert deployments["system_fingerprints"]
    cluster_version = cluster["version"]
    cluster_id = cluster["cluster_id"]
    cluster_nodes = cluster["nodes"]
    total_clusters = 0
    seen_nodes = []
    facts = details["sources"][0]["facts"]
    for fact in facts:
        if "node" in fact:
            assert fact["node"]["kind"] == "node"
            seen_nodes.append(fact["node"]["name"])
        if "cluster" in fact:
            assert fact["cluster"]["uuid"] == cluster_id
            assert fact["cluster"]["version"] == cluster_version
            total_clusters += 1
        if "projects" in fact:
            assert len(fact["projects"]) > 0
        if "workloads" in fact:
            assert len(fact["workloads"]) > 0
    assert total_clusters == 1, "Only one system fact should have a 'cluster' key"
    assert set(cluster_nodes) == set(seen_nodes), "The number of expected nodes diverged"
    #
    # Fingerprints
    #
    seen_nodes = []
    facts = deployments["system_fingerprints"]
    for fact in facts:
        assert fact["name"] in cluster_nodes
        assert fact["cpu_count"] > 0
        assert fact["architecture"] in ("x86_64",)
        seen_nodes.append(fact["name"])
    assert set(cluster_nodes) == set(seen_nodes), "The number of expected nodes diverged"


def validate_openshift_with_acm(cluster, details):
    EXPECTED_METRICS_KEYS = (
        "vendor",
        "cloud",
        "version",
        "managed_cluster_id",
        "available",
        "core_worker",
        "socket_worker",
        "created_via",
    )
    cluster_id = cluster["cluster_id"]
    # The last 'facts' in the list will contains cluster, operators and acm_metrics information
    acm_metrics = details["sources"][0]["facts"][-1]["acm_metrics"]
    assert (
        len(acm_metrics) > 1
    ), "Cluster has ACM and no metrics were detected (expected at least one)"
    assert cluster_id in [
        x["managed_cluster_id"] for x in acm_metrics
    ], "Cluster has ACM and its id is not in metrics"
    for metrics in acm_metrics:
        assert set(EXPECTED_METRICS_KEYS) == set(list(metrics))


@pytest.mark.parametrize(
    "cluster", config_openshift(), ids=(x["hostname"] for x in config_openshift())
)
def test_openshift_clusters(cluster, qpc_server_config):
    """Perform OpenShift inspection and validate results.

    :id: b7719be5-5473-424f-895d-022ea9ae55d5
    :description: Perform OpenShift inspection and validate cluster and nodes
        results.
    :steps:
        1. Add source with credential for a cluster
        2. Perform a scan
        3. Collect the report
    :expectedresults: The facts already knew about the cluster and nodes
        have expected values in deployment and details reports.
    """
    cred_name = utils.uuid4()
    cred_add_and_check(
        {"name": cred_name, "token": None, "type": "openshift"},
        [(AUTH_TOKEN_INPUT, cluster["token"])],
    )
    source_name = utils.uuid4()
    hostname = cluster["hostname"]
    port = cluster.get("port", 6443)
    ssl_cert_verify = not cluster["skip_tls_verify"]
    has_acm = "advanced-cluster-management" in cluster.get("operators", [])
    source_add_and_check(
        {
            "name": source_name,
            "cred": [cred_name],
            "hosts": [hostname],
            "port": port,
            "ssl-cert-verify": ssl_cert_verify,
            "type": "openshift",
        }
    )
    scan_name = utils.uuid4()
    scan_add_and_check({"name": scan_name, "sources": source_name})
    output = scan_start({"name": scan_name})
    match_scan_id = re.match(r'Scan "(\d+)" started.', output)
    assert match_scan_id is not None
    scan_job_id = match_scan_id.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    details, deployments = retrieve_report(scan_name, scan_job_id)
    validate_openshift_report(cluster, details, deployments)
    if has_acm:
        validate_openshift_with_acm(cluster, details)
