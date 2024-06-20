"""Tests for OpenShift sources.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import re

import pytest

from camayoc import utils
from camayoc.config import settings
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.cli.utils import retrieve_report
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import wait_for_scan
from camayoc.types.settings import SourceOptions


def validate_openshift_report(cluster, details, deployments):
    assert details["sources"]
    assert deployments["system_fingerprints"]
    total_clusters = 0
    seen_nodes = []
    for source in details["sources"]:
        for fact in source["facts"]:
            if "node" in fact:
                assert fact["node"]["kind"] == "node"
                seen_nodes.append(fact["node"]["name"])
            if "cluster" in fact:
                assert fact["cluster"]["uuid"] == cluster.cluster_id
                assert fact["cluster"]["version"] == cluster.version
                total_clusters += 1
            if "projects" in fact:
                assert len(fact["projects"]) > 0
            if "workloads" in fact:
                assert len(fact["workloads"]) > 0
    assert total_clusters == 1, "Only one system fact should have a 'cluster' key"
    assert set(cluster.nodes) == set(seen_nodes), "The number of expected nodes diverged"
    #
    # Fingerprints
    #
    seen_nodes = []
    facts = deployments["system_fingerprints"]
    for fact in facts:
        assert fact["name"] in cluster.nodes
        assert fact["cpu_count"] > 0
        assert fact["architecture"] in ("x86_64",)
        seen_nodes.append(fact["name"])
    assert set(cluster.nodes) == set(seen_nodes), "The number of expected nodes diverged"


def validate_node_metrics(cluster, details):
    has_node_metrics = False
    for source in details["sources"]:
        for fact in source["facts"]:
            if "node_metrics" in fact:
                has_node_metrics = True
                for metric in fact["node_metrics"]:
                    package = int(metric["package"])
                    assert package >= 0
                    assert metric["label_node_hyperthread_enabled"] in ("true", "false")
    assert has_node_metrics, "Could not found any node metrics."


def validate_operators(cluster, details):
    has_operators = False
    expected_operators = cluster.operators
    for source in details["sources"]:
        for fact in source["facts"]:
            if "operators" in fact:
                has_operators = True
                detected_operators = [operator["name"] for operator in fact["operators"]]
                for operator in expected_operators:
                    assert (
                        operator in detected_operators
                    ), f"The operator '{operator}' was not detected."
    assert has_operators, "Could not found any operators."


def validate_openshift_with_acm(cluster, details):
    EXPECTED_METRIC_KEYS = (
        "vendor",
        "cloud",
        "version",
        "managed_cluster_id",
        "available",
        "core_worker",
        "socket_worker",
        "created_via",
    )
    cluster_id = cluster.cluster_id
    for source in details["sources"]:
        for fact in source["facts"]:
            if "acm_metrics" in fact:
                acm_metrics = fact["acm_metrics"]
                assert (
                    len(acm_metrics) > 0
                ), "Cluster has ACM and no metrics were detected (expected at least one)."
                managed_clusters = [metric["managed_cluster_id"] for metric in acm_metrics]
                assert (
                    cluster_id in managed_clusters
                ), f"Cluster has ACM and its cluster-id 'f{cluster_id}' is not in metrics."
                for metric in acm_metrics:
                    assert set(EXPECTED_METRIC_KEYS) == set(list(metric))
                    assert metric["available"] in (True, False)
                    assert int(metric["core_worker"]) >= 0
                    assert int(metric["socket_worker"]) >= 0


def openshift_sources():
    for source_definition in settings.sources:
        if source_definition.type != "openshift":
            continue
        fixture_id = source_definition.name
        yield pytest.param(source_definition, id=fixture_id)


def openshift_cluster_info(name):
    for scan_info in settings.scans:
        if name in scan_info.sources:
            return scan_info.expected_data[scan_info.name].cluster_info


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_definition", openshift_sources())
def test_openshift_clusters(qpc_server_config, data_provider, source_definition: SourceOptions):
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
    source = data_provider.sources.new_one({"name": source_definition.name}, data_only=False)
    scan_name = utils.uuid4()
    scan_add_and_check({"name": scan_name, "sources": source.name})
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    output = scan_start({"name": scan_name})
    match_scan_id = re.match(r'Scan "(\d+)" started.', output)
    assert match_scan_id is not None
    scan_job_id = match_scan_id.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    details, deployments = retrieve_report(scan_job_id)
    cluster_info = openshift_cluster_info(source_definition.name)
    validate_openshift_report(cluster_info, details, deployments)
    validate_operators(cluster_info, details)
    validate_node_metrics(cluster_info, details)
    if "advanced-cluster-management" in cluster_info.operators:
        validate_openshift_with_acm(cluster_info, details)
