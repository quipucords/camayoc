# coding=utf-8
"""Tests for ``qpc report`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
import json
import os
import pprint
import random
import re
import tarfile

import pytest

from camayoc.qpc_models import Scan
from camayoc.tests.qpc.cli.csv_report_parsing import normalize_csv_report
from camayoc.utils import uuid4

from .utils import config_sources
from .utils import report_deployments
from .utils import report_detail
from .utils import report_download
from .utils import report_merge
from .utils import report_merge_status
from .utils import scan_add_and_check
from .utils import scan_job
from .utils import scan_start
from .utils import setup_qpc
from .utils import wait_for_report_merge
from .utils import wait_for_scan

# from csv_report_parsing import normalize_csv_report

REPORT_OUTPUT_FORMATS = ("csv", "json")
"""Valid report output formats."""

REPORT_SOURCE_OPTIONS = ("report", "scan-job")
"""Options to generate reports from."""

DEPLOYMENTS_REPORT_FIELDS = (
    "architecture",
    "bios_uuid",
    "cloud_provider",
    "cpu_core_count",
    "cpu_count",
    "cpu_hyperthreading",
    "cpu_socket_count",
    "entitlements",
    "etc_machine_id",
    "infrastructure_type",
    "insights_client_id",
    "ip_addresses",
    "is_redhat",
    "mac_addresses",
    "name",
    "os_name",
    "os_release",
    "os_version",
    "redhat_certs",
    "redhat_package_count",
    "sources",
    "subscription_manager_id",
    "system_addons",
    "system_creation_date",
    "system_last_checkin_date",
    "system_memory_bytes",
    "system_role",
    "system_service_level_agreement",
    "system_usage_type",
    "system_user_count",
    "user_login_history",
    "virtual_host_name",
    "virtual_host_uuid",
    "virtualized_type",
    "vm_cluster",
    "vm_datacenter",
    "vm_dns_name",
    "vm_host_core_count",
    "vm_host_socket_count",
    "vm_state",
    "vm_uuid",
)
"""Common deployments report expected fields."""

CSV_DEPLOYMENTS_REPORT_FIELDS = DEPLOYMENTS_REPORT_FIELDS + (
    "detection-ansible",
    "detection-network",
    "detection-openshift",
    "detection-satellite",
    "detection-vcenter",
    "jboss brms",
    "jboss eap",
    "jboss fuse",
    "jboss web server",
)
"""Deployments report expected fields for CSV output."""

JSON_DEPLOYMENTS_REPORT_FIELDS = DEPLOYMENTS_REPORT_FIELDS + (
    "cpu_core_per_socket",
    "deployment_report",
    "id",
    "metadata",
    "products",
    "system_platform_id",
    "system_purpose",
)
"""Deployments report expected fields for JSON output."""


FACTS = (
    "business_central_candidates",
    "business_central_candidates_eap",
    "cloud_provider",
    "connection_host",
    "connection_port",
    "connection_timestamp",
    "connection_uuid",
    "cpu_bogomips",
    "cpu_core_count",
    "cpu_core_per_socket",
    "cpu_count",
    "cpu_cpu_family",
    "cpu_hyperthreading",
    "cpu_model_name",
    "cpu_model_ver",
    "cpu_siblings",
    "cpu_socket_count",
    "cpu_vendor_id",
    "date_anaconda_log",
    "date_date",
    "date_filesystem_create",
    "date_machine_id",
    "date_yum_history",
    "decision_central_candidates",
    "decision_central_candidates_eap",
    "dmi_bios_vendor",
    "dmi_bios_version",
    "dmi_chassis_asset_tag",
    "dmi_processor_family",
    "dmi_system_manufacturer",
    "dmi_system_product_name",
    "dmi_system_uuid",
    "eap5_home_candidates",
    "eap5_home_ls_jboss_as",
    "eap5_home_readme_html",
    "eap5_home_run_jar_manifest",
    "eap5_home_run_jar_version",
    "eap5_home_version_txt",
    "eap_home_bin",
    "eap_home_candidates",
    "eap_home_jboss_modules_manifest",
    "eap_home_jboss_modules_version",
    "eap_home_layers",
    "eap_home_layers_conf",
    "eap_home_ls",
    "eap_home_readme_txt",
    "eap_home_version_txt",
    "etc_issue",
    "etc_machine_id",
    "etc_release_name",
    "etc_release_release",
    "etc_release_version",
    "fuse_activemq_version",
    "fuse_camel_version",
    "fuse_cxf_version",
    "host_done",
    "ifconfig_ip_addresses",
    "ifconfig_mac_addresses",
    "insights_client_id",
    "installed_products",
    "instnum",
    "jboss_activemq_ver",
    "jboss_brms_business_central_candidates",
    "jboss_brms_decision_central_candidates",
    "jboss_brms_drools_core_ver",
    "jboss_brms_kie_api_ver",
    "jboss_brms_kie_in_business_central",
    "jboss_brms_kie_server_candidates",
    "jboss_brms_kie_war_ver",
    "jboss_brms_locate_kie_api",
    "jboss_brms_manifest_mf",
    "jboss_camel_ver",
    "jboss_cxf_ver",
    "jboss_eap_chkconfig",
    "jboss_eap_common_files",
    "jboss_eap_find_jboss_modules_jar",
    "jboss_eap_find_jboss_modules_jar",
    "jboss_eap_id_jboss",
    "jboss_eap_jar_ver",
    "jboss_eap_jar_ver",
    "jboss_eap_locate_jboss_modules_jar",
    "jboss_eap_locate_jboss_modules_jar",
    "jboss_eap_packages",
    "jboss_eap_run_jar_ver",
    "jboss_eap_run_jar_ver",
    "jboss_eap_running_paths",
    "jboss_eap_systemctl_unit_files",
    "jboss_fuse_activemq_ver",
    "jboss_fuse_activemq_ver",
    "jboss_fuse_camel_ver",
    "jboss_fuse_camel_ver",
    "jboss_fuse_chkconfig",
    "jboss_fuse_cxf_ver",
    "jboss_fuse_cxf_ver",
    "jboss_fuse_on_eap_activemq_ver",
    "jboss_fuse_on_eap_camel_ver",
    "jboss_fuse_on_eap_cxf_ver",
    "jboss_fuse_on_karaf_activemq_ver",
    "jboss_fuse_on_karaf_camel_ver",
    "jboss_fuse_on_karaf_cxf_ver",
    "jboss_fuse_systemctl_unit_files",
    "jboss_processes",
    "jws_has_cert",
    "jws_has_eula_txt_file",
    "jws_home",
    "jws_home_candidates",
    "jws_installed_with_rpm",
    "jws_version",
    "karaf_find_karaf_jar",
    "karaf_home_bin_fuse",
    "karaf_home_system_org_jboss",
    "karaf_homes",
    "karaf_locate_karaf_jar",
    "karaf_running_processes",
    "kie_search_candidates",
    "kie_server_candidates",
    "kie_server_candidates_eap",
    "last_booted_at",
    "redhat_packages_certs",
    "redhat_packages_gpg_is_redhat",
    "redhat_packages_gpg_last_built",
    "redhat_packages_gpg_last_installed",
    "redhat_packages_gpg_num_installed_packages",
    "redhat_packages_gpg_num_rh_packages",
    "redhat_release_name",
    "redhat_release_release",
    "redhat_release_version",
    "subman",
    "subman_consumed",
    "subman_cpu_core_per_socket",
    "subman_cpu_cpu",
    "subman_cpu_cpu_socket",
    "subman_overall_status",
    "subman_virt_host_type",
    "subman_virt_is_guest",
    "subman_virt_uuid",
    "subscription_manager_id",
    "system_memory_bytes",
    "system_purpose_json",
    "system_user_count",
    "systemid",
    "tomcat_is_part_of_redhat_product",
    "uname_all",
    "uname_hardware_platform",
    "uname_hostname",
    "uname_kernel",
    "uname_os",
    "uname_processor",
    "user_has_sudo",
    "user_login_history",
    "virt_num_guests",
    "virt_num_running_guests",
    "virt_type",
    "virt_virt",
    "virt_what_type",
    "yum_enabled_repolist",
)
"""Common detail report expected facts."""

_SCANS = []
"""Global list of scans to generate reports from."""


def assert_json_report_fields(report_fields, expected_fields=JSON_DEPLOYMENTS_REPORT_FIELDS):
    """Assert that report fields are a subset of expected field."""
    report_fields = set(report_fields)
    expected_fields = set(expected_fields)
    assert report_fields.issubset(expected_fields), "Extra report fields: {}".format(
        report_fields - expected_fields
    )


@pytest.fixture(autouse=True, scope="module")
def setup_reports_prerequisites(data_provider):
    """Perform a couple of scans to generate reports from.

    Make sure there are two or more network sources on the config file and
    randomly choose two of them. Next, perform a scan for each network source
    and store the information about it on the global ``_SCANS`` list.
    """
    setup_qpc()
    network_sources = [source for source in config_sources() if source["type"] == "network"]
    random.shuffle(network_sources)
    network_sources = network_sources[:2]
    if len(network_sources) < 2:
        pytest.skip(
            "Make sure you have at least two network sources on the config "
            "file to run these tets."
        )

    for source in network_sources:
        real_source = data_provider.sources.new_one({"name": source["name"]}, data_only=False)
        scan = {"name": uuid4(), "sources": [real_source]}
        scan_add_and_check({"name": scan["name"], "sources": real_source.name})
        data_provider.mark_for_cleanup(Scan(name=scan["name"]))

        result = scan_start({"name": scan["name"]})
        match = re.match(r'Scan "(\d+)" started.', result)
        assert match is not None, result
        scan_job_id = match.group(1)
        scan["scan-job"] = scan_job_id
        wait_for_scan(scan_job_id)
        result = scan_job({"id": scan_job_id})
        assert result["status"] == "completed"
        report_id = result["report_id"]
        assert report_id is not None
        scan["report"] = report_id
        scan["json-file"] = os.path.abspath("{}.json".format(scan["name"]))
        report_detail({"json": None, "output-file": scan["json-file"], "report": scan["report"]})
        _SCANS.append(scan)
    yield
    for scan in _SCANS:
        os.remove(scan["json-file"])


@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize("output_format", REPORT_OUTPUT_FORMATS)
def test_deployments_report(source_option, output_format, isolated_filesystem, qpc_server_config):
    """Ensure a deployments report can be generated and has expected information.

    :id: 0ddfdd85-0836-46b5-9541-cf62b5d9c7bc
    :description: Ensure CSV and JSON deployments reports can be generated and
        have expected fields.
    :steps: Run ``qpc report deployments (--scan-job <scan-job-id> | --report
        <report-id>) (--json | --csv) --output-file <output-path>``
    :expectedresults: The generated report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    scan = random.choice(_SCANS)
    output_path = "{}.{}".format(uuid4(), output_format)
    output = report_deployments(
        {
            source_option: scan[source_option],
            output_format: None,
            "output-file": output_path,
        }
    )

    assert "Report written successfully." in output

    with open(output_path) as f:
        if output_format == "json":
            report = json.load(f)
            expected_fields = JSON_DEPLOYMENTS_REPORT_FIELDS
        else:
            report = normalize_csv_report(f, 5, [(0, 1)], report_type="deployments")
            expected_fields = CSV_DEPLOYMENTS_REPORT_FIELDS

    assert report["report_type"] == "deployments"
    for report_item in report["system_fingerprints"]:
        if output_format == "csv":
            # CSV reports must include all fields
            assert sorted(report_item.keys()) == sorted(expected_fields)
        else:
            # JSON reports will only diplay fields that are not null nor blank
            assert_json_report_fields(report_item.keys(), expected_fields)


@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize("output_format", REPORT_OUTPUT_FORMATS)
def test_detail_report(source_option, output_format, isolated_filesystem, qpc_server_config):
    """Ensure a detail report can be generated and has expected information.

    :id: 54fcfbb9-2435-4717-8693-8774b5c3643d
    :description: Ensure CSV and JSON detail reports can be generated and have
        expected fields.
    :steps: Run ``qpc report detail (--scan-job <scan-job-id> | --report
        <report-id>) (--json | --csv) --output-file <output-path>``
    :expectedresults: The generated report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    scan = random.choice(_SCANS)
    output_path = "{}.{}".format(uuid4(), output_format)
    output = report_detail(
        {
            "output-file": output_path,
            output_format: None,
            source_option: scan[source_option],
        }
    )

    assert "Report written successfully." in output

    with open(output_path) as f:
        if output_format == "json":
            report = json.load(f)
        else:
            # For CSV we need to massage the data a little bit. First ensure
            # there is a header with the report id, number of sources and
            # sources' information.
            report = normalize_csv_report(f, 8, [(0, 1), (5, 6)], report_type="detail")

    assert report["report_type"] == "details"
    assert len(report["sources"]) == len(scan["sources"])
    for report_source, scan_source in zip(report["sources"], scan["sources"]):
        assert "server_id" in report_source
        assert report_source["source_name"] == scan_source.name
        assert report_source["source_type"] == scan_source.source_type
        for facts in report_source["facts"]:
            report_facts = set(facts.keys())
            expected_facts = set(FACTS)
            assert report_facts.issubset(
                expected_facts
            ), "Extra report facts:\n{}\n\nExtra expected facts:\n{}".format(
                pprint.pformat(report_facts - expected_facts),
                pprint.pformat(expected_facts - report_facts),
            )


@pytest.mark.parametrize("merge_by", REPORT_SOURCE_OPTIONS + ("json-file",))
def test_merge_report(merge_by, isolated_filesystem, qpc_server_config):
    """Ensure can merge reports using report ids, scanjob ids and JSON files.

    :id: c47e37c0-3864-41d4-873d-276affdc6612
    :description: Ensure reports can be merged by report ids, scanjob ids and
        JSON files. Also ensure that the merged reports has the expected number
        of aggregated reports and each report has the expected fields.
    :steps:
        1) Run ``qpc report merge (--job-ids <scan-job-ids> | --report-ids
           <report-ids> | --json-files <json-files)``. Note the
           merged-report-id.
        2) Run ``qpc report deployments --report <merged-report-id>``.
        3) Ensure the merged report has the expected number of aggregated
           reports and each report have the expected fields.
    :expectedresults: The merged report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    if merge_by == "scan-job":
        merge_option = "job-ids"
    elif merge_by == "report":
        merge_option = "report-ids"
    elif merge_by == "json-file":
        merge_option = "json-files"
    else:
        pytest.fail('Unrecognized merge_by value: "{}"'.format(merge_by))
    merge_values = [str(scan[merge_by]) for scan in _SCANS]
    output = report_merge({merge_option: " ".join(merge_values)})

    match = re.search(r"Report merge job (\d+) created.", output)
    assert match is not None, output
    job_id = match.group(1)

    wait_for_report_merge(job_id)
    report_id = report_merge_status({"job": job_id})["report_id"]

    output_path = "{}.json".format(uuid4())
    output = report_deployments({"report": report_id, "json": None, "output-file": output_path})
    assert "Report written successfully." in output

    with open(output_path) as f:
        report = json.load(f)

    for report_item in report["system_fingerprints"]:
        assert_json_report_fields(report_item.keys())


@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
def test_download_report(source_option, isolated_filesystem, qpc_server_config):
    """Ensure a report can be downloaded and has expected information.

    :id: a8c8ef8c-fa64-11e8-82bb-8c1645a90ee2
    :description: Ensures reports can be downloaded in tar.gz format (ensures
        command fails if specified output not tar.gz) by report id, or scanjob
        id. Also ensures that package is not automatically extracted after
        download.
    :steps: Run ``qpc report download (--scan-job <scan-job-id> | --report
        <report-id>) --output-file <output-path>``
    :expectedresults: The downloaded report must be an un-extracted tar.gz
        package and must contain the expected report.
    """
    scan = random.choice(_SCANS)
    output_path = f"{uuid4()}"
    output_pkg = f"{output_path}.tar.gz"
    output = report_download({source_option: scan[source_option], "output-file": output_pkg})
    # Test that package downloaded
    assert "successfully written to" in output, (
        "Unexpected output from qpc report download! \n"
        'Expected to find "successfully written to" in output.'
        f"Actual output: {output}"
    )
    assert os.path.isfile(output_pkg), (
        "Unexpected output from qpc report download!\n"
        f"Download package not found at expected location: {output_pkg}"
    )

    # Test that tar isn't extracted
    pkg = tarfile.open(output_pkg)
    pkg_contents = pkg.getnames()

    pkg_top_contents = list(set(map(os.path.dirname, pkg_contents)))
    found_top_contents = list(filter(lambda src: src in os.listdir(), pkg_top_contents))
    assert not found_top_contents, (
        "Unexpected output from qpc report download!\n"
        f"Package appears to be extracted. Top level items of package found in \
        package's dir: {found_top_contents}"
    )

    # Test that fails on non-existant path
    missing_output_path = f"/no/such/number/{output_pkg})"
    with pytest.raises(AssertionError) as no_dir_exception_info:
        report_download({source_option: scan[source_option], "output-file": missing_output_path})
        expected_msg = "directory /no/such/number does not exist"
        assert no_dir_exception_info.match(expected_msg), (
            "Unexpected output from qpc report download! \n"
            f'Expected to find "{expected_msg}" in output, actual output was: \
            {str(no_dir_exception_info.value)}'
        )
        pytest.fail("I expected to fail with an AssertionError due to a missing directory")

    # Test that non tar.gz files fail
    non_tar_file = f"{format(uuid4())}"
    with pytest.raises(AssertionError) as tar_exception_info:
        report_download({source_option: scan[source_option], "output-file": non_tar_file})
        expected_tar_error = "extension is required to be tar.gz"
        assert tar_exception_info.match(expected_tar_error), (
            "Unexpected output from qpc report download!\n"
            f'Expected to find "{expected_tar_error}" in output, actual output \
            was: {str(no_dir_exception_info.value)}'
        )
        pytest.fail("I expected to fail with an AssertionError due to a bad output value specified")
