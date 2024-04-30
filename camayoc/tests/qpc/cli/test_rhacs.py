"""Tests for Red Hat Advanced Cluster Security sources.

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


def rhacs_sources():
    for source_definition in settings.sources:
        if source_definition.type != "rhacs":
            continue
        fixture_id = source_definition.name
        yield pytest.param(source_definition, id=fixture_id)


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_definition", rhacs_sources())
def test_rhacs_data(qpc_server_config, data_provider, source_definition: SourceOptions):
    """Perform Advanced Cluster Security scan and ensure data is valid and correct.

    :id: 6638b3e8-5001-40dc-9acd-23d652de6ec4
    :description: Perform Advanced Cluster Security scan and check if
        details report contain expected structure, as well as data
        matches basic expectations.
    :steps:
        1. Add source with credential for a RHACS
        2. Perform a scan
        3. Collect the report
    :expectedresults: Scan finishes, report can be downloaded, there are two
        basic facts (secured_units_max and secured_units_current), current Nodes
        and CPU units are not larger than max Nodes and CPU units.
    """
    source = data_provider.sources.new_one({"name": source_definition.name}, data_only=False)
    scan_name = uuid4()
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source.name,
        }
    )
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    # is often repeated, could be extracted / is extracted?
    # from here
    output = scan_start({"name": scan_name})
    match_scan_id = re.match(r'Scan "(\d+)" started.', output)
    assert match_scan_id is not None
    scan_job_id = match_scan_id.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    # to here
    details, deployments = retrieve_report(scan_job_id)
    for report_source in details.get("sources"):
        assert report_source.get("source_name") == source.name
        for fact in report_source.get("facts"):
            max_nodes = fact.get("secured_units_max").get("maxNodes")
            max_cpu_units = fact.get("secured_units_max").get("maxCpuUnits")
            current_nodes = fact.get("secured_units_current").get("numNodes")
            current_cpu_units = fact.get("secured_units_current").get("numCpuUnits")
            for max_date_key in ("maxNodesAt", "maxCpuUnitsAt"):
                assert fact.get("secured_units_max").get(max_date_key) is not None
            for numeric_value in (max_nodes, max_cpu_units, current_nodes, current_cpu_units):
                assert float(numeric_value) > 0
            assert float(max_nodes) >= float(current_nodes)
            assert float(max_cpu_units) >= float(current_cpu_units)
