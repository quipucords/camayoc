# coding=utf-8
"""Tests for ``qpc report`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import csv
import json
import os
import pprint
import random
import re

import pytest

from camayoc.utils import uuid4

from .utils import (
    config_sources,
    report_detail,
    report_merge,
    report_summary,
    scan_add_and_check,
    scan_job,
    scan_start,
    wait_for_scan,
)


REPORT_OUTPUT_FORMATS = ('csv', 'json')
"""Valid report output formats."""

REPORT_SOURCE_OPTIONS = ('report', 'scan-job')
"""Options to generate reports from."""

SUMMARY_REPORT_FIELDS = (
    'architecture',
    'bios_uuid',
    'cpu_core_count',
    'cpu_count',
    'cpu_socket_count',
    'entitlements',
    'infrastructure_type',
    'ip_addresses',
    'is_redhat',
    'mac_addresses',
    'name',
    'os_name',
    'os_release',
    'os_version',
    'redhat_certs',
    'redhat_package_count',
    'sources',
    'subscription_manager_id',
    'system_creation_date',
    'system_last_checkin_date',
    'virtualized_type',
    'vm_cluster',
    'vm_datacenter',
    'vm_dns_name',
    'vm_host',
    'vm_host_socket_count',
    'vm_state',
    'vm_uuid',
)
"""Common summary report expected fields."""

CSV_SUMMARY_REPORT_FIELDS = SUMMARY_REPORT_FIELDS + (
    'detection-network',
    'detection-satellite',
    'detection-vcenter',
    'jboss brms',
    'jboss eap',
    'jboss fuse',
    'jboss web server',
)
"""Summary report expected fields for CSV output."""

JSON_SUMMARY_REPORT_FIELDS = SUMMARY_REPORT_FIELDS + (
    'id',
    'metadata',
    'products',
    'report_id',
)
"""Summary report expected fields for JSON output."""


FACTS = (
    'business_central_candidates',
    'business_central_candidates_eap',
    'connection_host',
    'connection_port',
    'connection_timestamp',
    'connection_uuid',
    'cpu_bogomips',
    'cpu_core_count',
    'cpu_core_per_socket',
    'cpu_count',
    'cpu_cpu_family',
    'cpu_hyperthreading',
    'cpu_model_name',
    'cpu_model_ver',
    'cpu_siblings',
    'cpu_socket_count',
    'cpu_vendor_id',
    'date_anaconda_log',
    'date_date',
    'date_filesystem_create',
    'date_machine_id',
    'date_yum_history',
    'decision_central_candidates',
    'decision_central_candidates_eap',
    'dmi_bios_vendor',
    'dmi_bios_version',
    'dmi_processor_family',
    'dmi_system_manufacturer',
    'dmi_system_uuid',
    'eap5_home_candidates',
    'eap_home_candidates',
    'etc_issue',
    'etc_release_name',
    'etc_release_release',
    'etc_release_version',
    'fuse_activemq_version',
    'fuse_camel_version',
    'fuse_cxf_version',
    'ifconfig_ip_addresses',
    'ifconfig_mac_addresses',
    'jboss_brms_business_central_candidates',
    'jboss_brms_decision_central_candidates',
    'jboss_brms_kie_server_candidates',
    'jboss_brms_manifest_mf',
    'jboss_eap_chkconfig',
    'jboss_eap_common_files',
    'jboss_eap_id_jboss',
    'jboss_eap_packages',
    'jboss_eap_processes',
    'jboss_eap_running_paths',
    'jboss_eap_systemctl_unit_files',
    'jboss_fuse_chkconfig',
    'jboss_fuse_systemctl_unit_files',
    'jws_home_candidates',
    'jws_installed_with_rpm',
    'jws_version',
    'karaf_homes',
    'kie_search_candidates',
    'kie_server_candidates',
    'kie_server_candidates_eap',
    'redhat_packages_gpg_is_redhat',
    'redhat_packages_gpg_last_built',
    'redhat_packages_gpg_last_installed',
    'redhat_packages_gpg_num_installed_packages',
    'redhat_packages_gpg_num_rh_packages',
    'redhat_release_name',
    'redhat_release_release',
    'redhat_release_version',
    'subman_consumed',
    'subman_cpu_core_per_socket',
    'subman_cpu_cpu',
    'subman_cpu_cpu_socket',
    'subman_virt_host_type',
    'subman_virt_is_guest',
    'uname_all',
    'uname_hardware_platform',
    'uname_hostname',
    'uname_kernel',
    'uname_os',
    'uname_processor',
    'user_has_sudo',
    'virt_type',
    'virt_virt',
    'yum_enabled_repolist',
)
"""Common detail report expected facts."""

_SCANS = []
"""Global list of scans to generate reports from."""


@pytest.fixture(autouse=True, scope='module')
def setup_reports_prerequisites():
    """Perform a couple of scans to generate reports from.

    Make sure there are two or more network sources on the config file and
    randomly choose two of them. Next, perform a scan for each network source
    and store the information about it on the global ``_SCANS`` list.
    """
    network_sources = [
        source for source in config_sources()
        if source['type'] == 'network'
    ]
    random.shuffle(network_sources)
    network_sources = network_sources[:2]
    if len(network_sources) < 2:
        pytest.skip(
            'Make sure you have at least two network sources on the config '
            'file to run these tets.'
        )

    for source in network_sources:
        scan = {
            'name': uuid4(),
            'sources': [source],
        }
        scan_add_and_check({
            'name': scan['name'],
            'sources': source['name'],
        })

        result = scan_start({
            'name': scan['name'],
        })
        match = re.match(r'Scan "(\d+)" started.', result)
        assert match is not None
        scan_job_id = match.group(1)
        scan['scan-job'] = scan_job_id
        wait_for_scan(scan_job_id)
        result = scan_job({
            'id': scan_job_id,
        })
        assert result['status'] == 'completed'
        report_id = result['report_id']
        assert report_id is not None
        scan['report'] = report_id
        scan['json-file'] = os.path.abspath('{}.json'.format(scan['name']))
        report_detail({
            'json': None,
            'output-file': scan['json-file'],
            'report': scan['report'],
        })
        _SCANS.append(scan)
    yield
    for scan in _SCANS:
        os.remove(scan['json-file'])


@pytest.mark.parametrize('source_option', REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize('output_format', REPORT_OUTPUT_FORMATS)
def test_summary_report(
        source_option, output_format, isolated_filesystem, qpc_server_config):
    """Ensure a summary report can be generated and has expected information.

    :id: 0ddfdd85-0836-46b5-9541-cf62b5d9c7bc
    :description: Ensure CSV and JSON summary reports can be generated and
        have expected fields.
    :steps: Run ``qpc report summary (--scan-job <scan-job-id> | --report
        <report-id>) (--json | --csv) --output-file <output-path>``
    :expectedresults: The generated report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    scan = random.choice(_SCANS)
    output_path = '{}.{}'.format(uuid4(), output_format)
    output = report_summary({
        source_option: scan[source_option],
        output_format: None,
        'output-file': output_path,
    })

    assert output.strip() == 'Report written successfully..'

    with open(output_path) as f:
        if output_format == 'json':
            report = json.load(f)
            expected_fields = JSON_SUMMARY_REPORT_FIELDS
        else:
            # For CSV we need to massage the data a little bit. First ensure
            # there is a header with the report id and the report section.
            header = ''.join(f.readline() for _ in range(5))
            assert header == 'Report\n{}\n\n\nReport:\n'.format(
                scan['report'])
            # Now that we extracted the header we can call the CSV reader to
            # read the report information
            reader = csv.DictReader(f)
            # Finally normalize the information to match what is returned by
            # the JSON format so we can do assertion later.
            report = {
                'report': [row for row in reader],
                'report_id': header.splitlines()[1],
            }
            expected_fields = CSV_SUMMARY_REPORT_FIELDS

    for report_item in report['report']:
        assert sorted(report_item.keys()) == sorted(expected_fields)


@pytest.mark.parametrize('source_option', REPORT_SOURCE_OPTIONS)
@pytest.mark.parametrize('output_format', REPORT_OUTPUT_FORMATS)
def test_detail_report(
        source_option, output_format, isolated_filesystem, qpc_server_config):
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
    output_path = '{}.{}'.format(uuid4(), output_format)
    output = report_detail({
        'output-file': output_path,
        output_format: None,
        source_option: scan[source_option],
    })

    assert output.strip() == 'Report written successfully..'

    with open(output_path) as f:
        if output_format == 'json':
            report = json.load(f)
        else:
            # For CSV we need to massage the data a little bit. First ensure
            # there is a header with the report id, number of sources and
            # sources' information.
            headers = [f.readline() for _ in range(8)]
            report_id, number_sources = headers[1].strip().split(',')
            server_id, source_name, source_type = headers[6].strip().split(',')
            # Now that we extracted the header we can call the CSV reader to
            # read the report information
            reader = csv.DictReader(f)
            # Finally normalize the information to match what is returned by
            # the JSON format so we can do assertion later.
            report = {
                'id': report_id,
                'sources': [{
                    'facts': [row for row in reader],
                    'server_id': server_id,
                    'source_name': source_name,
                    'source_type': source_type,
                }],
            }

    assert len(report['sources']) == len(scan['sources'])
    for report_source, scan_source in zip(report['sources'], scan['sources']):
        assert 'server_id' in report_source
        assert report_source['source_name'] == scan_source['name']
        assert report_source['source_type'] == scan_source['type']
        for facts in report_source['facts']:
            report_facts = set(facts.keys())
            expected_facts = set(FACTS)
            assert report_facts.issubset(expected_facts), (
                'Extra report facts:\n{}\n\nExtra expected facts:\n{}'.format(
                    pprint.pformat(report_facts - expected_facts),
                    pprint.pformat(expected_facts - report_facts),
                )
            )


@pytest.mark.parametrize('merge_by', REPORT_SOURCE_OPTIONS + ('json-file',))
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
        2) Run ``qpc report summary --report <merged-report-id>``.
        3) Ensure the merged report has the expected number of aggregated
           reports and each report have the expected fields.
    :expectedresults: The merged report must be on the requested format
        (either CSV or JSON) and must have the expected fields.
    """
    if merge_by == 'scan-job':
        merge_option = 'job-ids'
    elif merge_by == 'report':
        merge_option = 'report-ids'
    elif merge_by == 'json-file':
        merge_option = 'json-files'
    else:
        pytest.fail('Unrecognized merge_by value: "{}"'.format(merge_by))
    merge_values = [str(scan[merge_by]) for scan in _SCANS]
    output = report_merge({
        merge_option: ' '.join(merge_values),
    })

    match = re.match(
        r'Scan job results successfully merged.  Report ID is (\d+).',
        output
    )
    assert match is not None
    report_id = match.group(1)

    output_path = '{}.json'.format(uuid4())
    output = report_summary({
        'report': report_id,
        'json': None,
        'output-file': output_path,
    })
    assert output.strip() == 'Report written successfully..'

    with open(output_path) as f:
        report = json.load(f)

    assert len(report['report']) == len(_SCANS)

    for report_item in report['report']:
        assert sorted(report_item.keys()) == sorted(JSON_SUMMARY_REPORT_FIELDS)
