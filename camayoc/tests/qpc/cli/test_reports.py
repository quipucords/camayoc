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
import re
import tarfile
from copy import deepcopy
from functools import partial
from operator import itemgetter
from pathlib import Path
from typing import Iterable

import pytest
from littletable import Table

from camayoc.constants import QPC_SOURCE_TYPES
from camayoc.qpc_models import Report
from camayoc.qpc_models import Source
from camayoc.tests.qpc.cli.csv_report_parsing import normalize_csv_report
from camayoc.types.scans import FinishedScan
from camayoc.types.settings import SourceOptions
from camayoc.utils import uuid4

from .utils import report_aggregate
from .utils import report_deployments
from .utils import report_detail
from .utils import report_download
from .utils import report_insights
from .utils import report_merge
from .utils import report_upload
from .utils import scan_job
from .utils import wait_for_scan

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
    "installed_products",
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

VCENTER_CSV_DEPLOYMENTS_REPORT_FIELDS = DEPLOYMENTS_REPORT_FIELDS + (
    "detection-rhacs",
    "detection-ansible",
    "detection-network",
    "detection-openshift",
    "detection-satellite",
    "detection-vcenter",
)
"""Deployments report expected fields for CSV output in VCenter scan."""

CSV_DEPLOYMENTS_REPORT_FIELDS = VCENTER_CSV_DEPLOYMENTS_REPORT_FIELDS + (
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
    "hostnamectl",
    "ifconfig_ip_addresses",
    "ifconfig_mac_addresses",
    "insights_client_id",
    "installed_products",
    "instnum",
    "internal_cpu_model_name_kvm",
    "internal_cpu_socket_count_cpuinfo",
    "internal_cpu_socket_count_dmi",
    "internal_distro_standard_release",
    "internal_dmi_chassis_asset_tag",
    "internal_dmi_system_product_name",
    "internal_dmi_system_uuid",
    "internal_have_chkconfig",
    "internal_have_dmidecode",
    "internal_have_ifconfig",
    "internal_have_ip",
    "internal_have_java",
    "internal_have_locate",
    "internal_have_rct",
    "internal_have_rpm",
    "internal_have_subscription_manager",
    "internal_have_systemctl",
    "internal_have_tune2fs",
    "internal_have_unzip",
    "internal_have_virsh",
    "internal_have_virt_what",
    "internal_have_yum",
    "internal_host_started_processing_role",
    "internal_kvm_found",
    "internal_release_file",
    "internal_sys_manufacturer",
    "internal_system_user_count",
    "internal_user_login_history",
    "internal_virt_what_error",
    "internal_xen_guest",
    "internal_xen_privcmd_found",
    "ip_address_show_ipv4",
    "ip_address_show_mac",
    "jboss_activemq_ver",
    "jboss_camel_ver",
    "jboss_cxf_ver",
    "jboss_eap_chkconfig",
    "jboss_eap_common_files",
    "jboss_eap_find_jboss_modules_jar",
    "jboss_eap_id_jboss",
    "jboss_eap_jar_ver",
    "jboss_eap_locate_jboss_modules_jar",
    "jboss_eap_packages",
    "jboss_eap_run_jar_ver",
    "jboss_eap_running_paths",
    "jboss_eap_systemctl_unit_files",
    "jboss_fuse_activemq_ver",
    "jboss_fuse_camel_ver",
    "jboss_fuse_chkconfig",
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


def assert_json_report_fields(report_fields, expected_fields=JSON_DEPLOYMENTS_REPORT_FIELDS):
    """Assert that report fields are a subset of expected field."""
    report_fields = set(report_fields)
    expected_fields = set(expected_fields)
    assert report_fields.issubset(expected_fields), "Extra report fields: {}".format(
        report_fields - expected_fields
    )


def scan_with_source_type(source_types, data_provider, scans) -> FinishedScan:
    """Obtain a scan that uses a source of type specified in argument."""
    scan_source = data_provider.sources.defined_one({"type": Table.is_in(source_types)})

    def contains_source(sources):
        return scan_source.name in sources

    scan = data_provider.scans.defined_one({"sources": contains_source})
    finished_scan = scans.with_name(scan.name)
    assert finished_scan.report_id, f"No report id was returned from scan {scan.name}"

    return finished_scan


def scan_sources(finished_scan: FinishedScan, data_provider) -> Iterable[SourceOptions]:
    """List of source configuration objects used by a specific scan."""
    scan_sources = finished_scan.definition.sources
    sources = data_provider.sources._defined_models.where(name=Table.is_in(scan_sources))
    sources = [source for source in sources]
    return sources


def source_option_attr(source_option, finished_scan):
    """Obtain a relevant source_option-mapped value from FinishedScan."""
    attr_name = source_option.replace("-", "_") + "_id"
    return getattr(finished_scan, attr_name)


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize("output_format", REPORT_OUTPUT_FORMATS)
def test_deployments_report(  # noqa: PLR0913
    source_option, output_format, data_provider, scans, isolated_filesystem, qpc_server_config
):
    """Ensure a deployments report can be generated and has expected information.

    :id: 0ddfdd85-0836-46b5-9541-cf62b5d9c7bc
    :description: Ensure CSV and JSON deployments reports can be generated and
        have expected fields.
    :steps: Run ``qpc report deployments (--scan-job <scan-job-id> | --report
        <report-id>) (--json | --csv) --output-file <output-path>``
    :expectedresults: The generated report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    finished_scan = scan_with_source_type(("network", "satellite", "vcenter"), data_provider, scans)
    sources = scan_sources(finished_scan, data_provider)
    sources_names = [source.name for source in sources]
    sources_types = [source.type for source in sources]

    output_path = "{}.{}".format(uuid4(), output_format)

    output = report_deployments(
        {
            source_option: source_option_attr(source_option, finished_scan),
            output_format: None,
            "output-file": output_path,
        }
    )

    assert "Report written successfully." in output

    with open(output_path) as f:
        if output_format == "json":
            report = json.load(f)
            expected_fields = JSON_DEPLOYMENTS_REPORT_FIELDS
            scan_report_id = finished_scan.report_id
        else:
            report = normalize_csv_report(f, 5, [(0, 1)], report_type="deployments")
            expected_fields = CSV_DEPLOYMENTS_REPORT_FIELDS
            if "vcenter" in sources_types:
                expected_fields = VCENTER_CSV_DEPLOYMENTS_REPORT_FIELDS
            scan_report_id = str(finished_scan.report_id)

    assert report["report_type"] == "deployments"
    assert report["report_id"] == scan_report_id
    assert report["report_platform_id"]
    assert report["report_version"]
    if output_format == "json":
        assert report["status"] == "completed"
    for report_item in report["system_fingerprints"]:
        if output_format == "csv":
            # CSV reports must include all fields
            assert sorted(report_item.keys()) == sorted(expected_fields)
        else:
            # JSON reports will only diplay fields that are not null nor blank
            assert_json_report_fields(report_item.keys(), expected_fields)

    if output_format == "csv":
        return

    known_source_names = [
        source["source_name"]
        for fingerprint in report["system_fingerprints"]
        for source in fingerprint["sources"]
    ]
    known_source_types = [
        source["source_type"]
        for fingerprint in report["system_fingerprints"]
        for source in fingerprint["sources"]
    ]
    assert any(source_name in known_source_names for source_name in sources_names)
    assert any(source_type in known_source_types for source_type in sources_types)
    for fingerprint in report["system_fingerprints"]:
        fingerprint_keys = set(fingerprint.keys())
        metadata_keys = set(fingerprint["metadata"].keys())
        assert not (metadata_keys - fingerprint_keys)
        for metadata in fingerprint["metadata"].values():
            assert "has_sudo" in metadata
            assert "raw_fact_key" in metadata
            assert "server_id" in metadata
            assert "source_name" in metadata
            assert "source_type" in metadata


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize("output_format", REPORT_OUTPUT_FORMATS)
def test_detail_report(  # noqa: PLR0913
    source_option, output_format, data_provider, scans, isolated_filesystem, qpc_server_config
):
    """Ensure a detail report can be generated and has expected information.

    :id: 54fcfbb9-2435-4717-8693-8774b5c3643d
    :description: Ensure CSV and JSON detail reports can be generated and have
        expected fields.
    :steps: Run ``qpc report detail (--scan-job <scan-job-id> | --report
        <report-id>) (--json | --csv) --output-file <output-path>``
    :expectedresults: The generated report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    finished_scan = scan_with_source_type(("network",), data_provider, scans)
    sources = scan_sources(finished_scan, data_provider)
    sources_names = [source.name for source in sources]
    sources_types = [source.type for source in sources]

    output_path = "{}.{}".format(uuid4(), output_format)
    output = report_detail(
        {
            "output-file": output_path,
            output_format: None,
            source_option: source_option_attr(source_option, finished_scan),
        }
    )

    assert "Report written successfully." in output

    with open(output_path) as f:
        if output_format == "json":
            report = json.load(f)
            scan_report_id = finished_scan.report_id
            number_sources = len(report["sources"])
        else:
            # For CSV we need to massage the data a little bit. First ensure
            # there is a header with the report id, number of sources and
            # sources' information.
            report = normalize_csv_report(f, 8, [(0, 1), (5, 6)], report_type="detail")
            scan_report_id = str(finished_scan.report_id)
            number_sources = int(report["number_sources"])

    assert report["report_type"] == "details"
    assert report["report_id"] == scan_report_id
    assert report["report_platform_id"]
    assert report["report_version"]
    assert len(sources_names) == number_sources
    for report_source in report["sources"]:
        assert "server_id" in report_source
        assert report_source["source_name"] in sources_names
        assert report_source["source_type"] in sources_types
        if output_format == "json":
            assert report_source["report_version"]
            assert report_source["report_version"] == report["report_version"]
        for facts in report_source["facts"]:
            report_facts = set(facts.keys())
            expected_facts = set(FACTS)
            assert report_facts.issubset(
                expected_facts
            ), "Extra report facts:\n{}\n\nExtra expected facts:\n{}".format(
                pprint.pformat(report_facts - expected_facts),
                pprint.pformat(expected_facts - report_facts),
            )


@pytest.mark.runs_scan
@pytest.mark.parametrize("merge_by", REPORT_SOURCE_OPTIONS + ("json-file",))
def test_merge_report(merge_by, data_provider, scans, isolated_filesystem, qpc_server_config):
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
    expected_source_types = set(("network", "satellite", "vcenter"))
    found_scans = []
    scan_generator = data_provider.scans.defined_many({})
    for scan in scan_generator:
        source_types = set()
        for source_id in scan.sources:
            source = Source(client=scan.client, _id=source_id)
            source_data = source.read().json()
            source_types.add(source_data.get("source_type"))

        if not expected_source_types.intersection(source_types):
            continue

        finished_scan = scans.with_name(scan.name)
        assert finished_scan.report_id, f"No report id was returned from scan {scan.name}"
        found_scans.append(finished_scan)

        if len(found_scans) >= 2:
            break

    if merge_by == "scan-job":
        merge_option = "job-ids"
        merge_values = [str(scan.scan_job_id) for scan in found_scans]
    elif merge_by == "report":
        merge_option = "report-ids"
        merge_values = [str(scan.report_id) for scan in found_scans]
    elif merge_by == "json-file":
        merge_option = "json-files"
        merge_values = []
        for scan in found_scans:
            json_file = Path(f"{scan.definition.name}-{uuid4()}.json").resolve().as_posix()
            report_detail({"json": None, "output-file": json_file, "report": scan.report_id})
            merge_values.append(json_file)
    else:
        pytest.fail('Unrecognized merge_by value: "{}"'.format(merge_by))

    output = report_merge({merge_option: " ".join(merge_values)})

    match = re.search(r"Report merge job (\d+) created.", output)
    assert match is not None, output
    job_id = match.group(1)

    wait_for_scan(job_id)
    report_id = scan_job({"id": job_id})["report_id"]

    output_path = "{}.json".format(uuid4())
    output = report_deployments({"report": report_id, "json": None, "output-file": output_path})
    assert "Report written successfully." in output

    with open(output_path) as f:
        report = json.load(f)

    for report_item in report["system_fingerprints"]:
        assert_json_report_fields(report_item.keys())


@pytest.mark.runs_scan
def test_upload_report(data_provider, scans, isolated_filesystem, qpc_server_config, tmp_path):
    """Ensure can upload reports using JSON files.

    :id: fb661698-4cc7-4b6e-9964-a006633eb5af
    :description: Ensure (JSON) details reports can be uploaded. Also ensure
        that that uploaded report has been successfully processed by generating
        a deployments report.
    :steps:
        1) Run ``qpc report upload --json-file <json-file>``. Note the
           job_id and report_id.
        2) Wait until job completion (``qpc scan job --id <job_id>``).
        3) Collect details report.
        4) Ensure details report is equivalent to the original report.
        5) Collect deployments report.
        6) Ensure the deployments report is equivalent to the original report.
    :expectedresults: The details and deployments report must be on the requested format
        (JSON) and must have contents equivalent to the original report.
    """

    def _get_from_keys(*keys):
        """
        Return a function that will get the value of dicts by certain keys.

        This is intended to be used later as the "key" argument for `sorted`.
        """

        def _getter(_dict):
            # coerce to values to str to avoid issues comparing different types
            return tuple(str(_dict.get(key)) for key in keys)

        return _getter

    def _get_comparable_source_list(details_report_json):
        """Return a list of comparable 'sources' from details report."""
        # preserve the original data
        source_list = deepcopy(details_report_json["sources"])
        # given source names are uuids, let's use those to order sources
        source_list = sorted(source_list, key=itemgetter("source_name"))
        for source_dict in source_list:
            # sort facts by unique facts for network, satellite and vcenter
            sorted_facts = sorted(
                source_dict.pop("facts", []),
                key=_get_from_keys(
                    "connection_uuid", "uuid", "vm.uuid", "vm.name", "hostname", "connection_host"
                ),
            )
            source_dict["facts"] = sorted_facts
        return source_list

    finished_scan = scan_with_source_type(("network", "satellite", "vcenter"), data_provider, scans)
    path_to_details_report = tmp_path / "original-report.json"
    path_to_details_report.write_text(json.dumps(finished_scan.details_report))
    output = report_upload({"json-file": path_to_details_report})
    match = re.search(r"Report uploaded. Job (\d+) created.", output)
    assert match is not None, output
    job_id = match.group(1)
    wait_for_scan(job_id)
    report = Report()
    report.retrieve_from_scan_job(scan_job_id=job_id)

    # compare details report
    uploaded_report = report.details().json()
    original_report = finished_scan.details_report
    assert (
        original_report["report_type"] == "details" and uploaded_report["report_type"] == "details"
    )
    equal_fields = {}
    for field in ("report_id", "report_platform_id"):
        if original_report[field] == uploaded_report[field]:
            equal_fields.add(field)
    assert not equal_fields, (
        "Uploaded report has fields that should not be equal to the original: %s"
        % ", ".join(equal_fields)
    )
    source_list1 = _get_comparable_source_list(original_report)
    source_list2 = _get_comparable_source_list(uploaded_report)
    assert source_list1 == source_list2

    # compare deployments report
    uploaded_deployments = report.deployments().json()
    for report_item in uploaded_deployments["system_fingerprints"]:
        assert_json_report_fields(report_item.keys())
    fingerprint_sorter = partial(
        sorted, key=_get_from_keys("bios_uuid", "vm_uuid", "subscription_manager_id", "name")
    )

    original_fingerprints = fingerprint_sorter(
        deepcopy(finished_scan.deployments_report["system_fingerprints"])
    )
    uploaded_fingerprints = fingerprint_sorter(uploaded_deployments["system_fingerprints"])
    # remove id & deployment_report from comparison as these fields are expected to be distinct
    [(f.pop("id"), f.pop("deployment_report")) for f in original_fingerprints]
    [(f.pop("id"), f.pop("deployment_report")) for f in uploaded_fingerprints]
    assert original_fingerprints == uploaded_fingerprints


@pytest.mark.runs_scan
@pytest.mark.parametrize("source_option", REPORT_SOURCE_OPTIONS)
def test_download_report(
    source_option, data_provider, scans, isolated_filesystem, qpc_server_config
):
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
    finished_scan = scan_with_source_type(("network", "satellite", "vcenter"), data_provider, scans)

    output_pkg = f"{uuid4()}.tar.gz"

    output = report_download(
        {source_option: source_option_attr(source_option, finished_scan), "output-file": output_pkg}
    )
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
        report_download(
            {
                source_option: source_option_attr(source_option, finished_scan),
                "output-file": missing_output_path,
            }
        )
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
        report_download(
            {
                source_option: source_option_attr(source_option, finished_scan),
                "output-file": non_tar_file,
            }
        )
        expected_tar_error = "extension is required to be tar.gz"
        assert tar_exception_info.match(expected_tar_error), (
            "Unexpected output from qpc report download!\n"
            f'Expected to find "{expected_tar_error}" in output, actual output \
            was: {str(no_dir_exception_info.value)}'
        )
        pytest.fail("I expected to fail with an AssertionError due to a bad output value specified")


@pytest.mark.runs_scan
def test_download_insights_report(data_provider, scans, isolated_filesystem, qpc_server_config):
    """Ensure insights report can be downloaded.

    :id: 3f5e87c2-8a4d-42a0-afda-6fcaf77142c3
    :description: Request insights report file, download it and verify
        it appears to be correct. Full upload-verify hosts-verify
        subscriptions flow is tested by iqe-foreman-rh-cloud-plugin.
    :steps:
        1) Run ``qpc report insights --report <report id>
           --output-file <path>``.
        2) Verify that command succeeded.
        3) Verify that downloaded archive looks like valid
           insights archive.
    :expectedresults: Report is downloaded and content matches
        insights archive format.
    """
    finished_scan = scan_with_source_type(("network",), data_provider, scans)

    output_file = f"insights-{uuid4()}.tar.gz"

    output = report_insights({"report": finished_scan.report_id, "output-file": output_file})

    assert "Report written successfully" in output
    assert os.path.isfile(
        output_file
    ), f"Insights report not found at (failed download?): {output_file}"

    tar = tarfile.open(output_file)
    tar_content = {"report_slices": {}}
    for filename in tar.getnames():
        file_fh = tar.extractfile(filename)
        assert file_fh, f"Broken tar archive: {filename}"
        file_content = json.load(file_fh)
        if filename.endswith("metadata.json"):
            tar_content["metadata.json"] = file_content
        else:
            key = Path(filename).stem
            hosts_num = len(file_content.get("hosts", []))
            tar_content["report_slices"][key] = {"number_hosts": hosts_num}

    assert "metadata.json" in tar_content, "Insights report does not have metadata.json file"
    assert (
        tar_content["metadata.json"].get("report_slices", {}) == tar_content["report_slices"]
    ), "Data in metadata.json and actual data in archive do not match"


@pytest.mark.runs_scan
def test_download_aggregate_report(data_provider, scans, isolated_filesystem, qpc_server_config):
    """Ensure aggregate report can be downloaded.

    :id: 3e772a6a-c8b1-48b4-aee0-9a636afaf000
    :description: Request aggregate report, download it and verify
        it appears to be correct.
    :steps:
        1) Run ``qpc report aggregate --report <report id>``.
        2) Verify that command succeeded.
        3) Verify that downloaded data looks like valid JSON.
    :expectedresults: Report is downloaded and data is valid JSON.
    """
    finished_scan = scan_with_source_type(QPC_SOURCE_TYPES, data_provider, scans)
    output_file = f"aggregate-{uuid4()}.json"
    output = report_aggregate({"report": finished_scan.report_id, "output-file": output_file})

    assert "Report written successfully" in output
    assert os.path.isfile(
        output_file
    ), f"Aggregate report not found at (failed download?): {output_file}"

    with open(output_file) as fh:
        json_formatted = json.load(fh)
    assert len(json_formatted)
