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
import re
import time
from pprint import pformat

import pexpect

import pytest

from camayoc.config import get_config
from camayoc.constants import (BECOME_PASSWORD_INPUT,
                               CONNECTION_PASSWORD_INPUT,
                               QPC_BRMS_EXTENDED_FACTS,
                               QPC_BRMS_RAW_FACTS,
                               QPC_EAP_EXTENDED_FACTS,
                               QPC_EAP_RAW_FACTS,
                               QPC_FUSE_EXTENDED_FACTS,
                               QPC_FUSE_RAW_FACTS)
from camayoc.exceptions import (
    ConfigFileNotFoundError,
    FailedScanException,
    WaitTimeError,
)
from camayoc.utils import name_getter, uuid4

from .conftest import qpc_server_config
from .utils import (
    cred_add_and_check,
    report_detail,
    scan_add_and_check,
    scan_cancel,
    scan_job,
    scan_pause,
    scan_restart,
    scan_start,
    source_add_and_check,
)


def config_credentials():
    """Return all credentials available on configuration file."""
    try:
        return get_config().get('credentials', [])
    except ConfigFileNotFoundError:
        return []


def config_sources():
    """Return all sources available on configuration file."""
    try:
        return get_config().get('qpc', {}).get('sources', [])
    except ConfigFileNotFoundError:
        return []


@pytest.fixture(params=config_credentials(), ids=name_getter)
def credentials(request):
    """Return each credential available on the config file."""
    return request.param


@pytest.fixture(params=config_sources(), ids=name_getter)
def source(request):
    """Return each source available on the config file."""
    return request.param


@pytest.fixture(autouse=True, scope='module')
def setup_credentials():
    """Create all credentials on the server."""
    qpc_server_config()

    qpc_cred_clear = pexpect.spawn(
        'qpc cred clear --all'
    )
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()

    credentials = get_config().get('credentials', [])
    for credential in credentials:
        inputs = []
        if 'password' in credential:
            inputs.append((CONNECTION_PASSWORD_INPUT, credential['password']))
            credential['password'] = None
        if 'become-password' in credential:
            inputs.append(
                (BECOME_PASSWORD_INPUT, credential['become-password']))
            credential['become-password'] = None
        cred_add_and_check(credential, inputs)


@pytest.fixture(autouse=True, scope='module')
def setup_sources():
    """Create all sources on the server."""
    qpc_server_config()

    qpc_cred_clear = pexpect.spawn(
        'qpc source clear --all'
    )
    assert qpc_cred_clear.expect(pexpect.EOF) == 0
    qpc_cred_clear.close()

    sources = get_config().get('qpc', {}).get('sources', [])
    for source in sources:
        source['cred'] = source.pop('credentials')
        options = source.pop('options', {})
        for k, v in options.items():
            source[k.replace('_', '-')] = v
        source_add_and_check(source)


def wait_for_scan(scan_job_id, status='completed', timeout=900):
    """Wait for a scan to reach some ``status`` up to ``timeout`` seconds.

    :param scan_job_id: Scan ID to wait for.
    :param status: Scan status which will wait for. Default is completed.
    :param timeout: wait up to this amount of seconds. Default is 900.
    """
    while timeout > 0:
        result = scan_job({'id': scan_job_id})
        if status != 'failed' and result['status'] == 'failed':
            raise FailedScanException(
                'The scan with ID "{}" has failed unexpectedly.\n\n'
                'The information about the scan is:\n{}\n'
                .format(scan_job_id, pformat(result))
            )
        if result['status'] == status:
            return
        time.sleep(5)
        timeout -= 5
    raise WaitTimeError(
        'Timeout waiting for scan with ID "{}" to achieve the "{}" status.\n\n'
        'The information about the scan is:\n{}\n'
        .format(scan_job_id, status, pformat(result))
    )


@pytest.mark.troubleshoot
def test_scanjob(isolated_filesystem, qpc_server_config, source):
    """Scan a single source type.

    :id: 49ae6fef-ea41-4b91-b310-6054678bfbb4
    :description: Perform a scan on a single source type.
    :steps: Run ``qpc scan start --sources <source>``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    scan_name = uuid4()
    scan_add_and_check({
        'name': scan_name,
        'sources': config_sources()[0]['name'],
    })

    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id)
    result = scan_job({
        'id': scan_job_id,
    })
    assert result['status'] == 'completed'
    report_id = result['report_id']
    assert report_id is not None
    output_file = 'out.json'
    report = report_detail({
        'json': None,
        'output-file': output_file,
        'report': report_id,
    })
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get('sources', []) != []


def test_scanjob_with_multiple_sources(isolated_filesystem, qpc_server_config):
    """Scan multiple source types.

    :id: 58fde39c-52d8-42ee-af4c-1d75a6dc80b0
    :description: Perform a scan on multiple source types.
    :steps: Run ``qpc scan start --sources <source1> <source2> ...``
    :expectedresults: The scan must completed without any error and a report
        should be available.
    """
    scan_name = uuid4()
    scan_add_and_check({
        'name': scan_name,
        'sources': ' '.join([source['name'] for source in config_sources()]),
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({
        'id': scan_job_id,
    })
    assert result['status'] == 'completed'
    report_id = result['report_id']
    assert report_id is not None
    output_file = 'out.json'
    report = report_detail({
        'json': None,
        'output-file': output_file,
        'report': report_id,
    })
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get('sources', []) != []


def test_scanjob_with_disabled_products(isolated_filesystem,
                                        qpc_server_config):
    """Perform a scan with an optional products disabled.

    :id: 3e01ea6c-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with optional products disabled and assert
        that the product facts are not collected in the report.
    :steps:
        1) Add a scan using the scan_add_and_check function
        2) Start the scan and check that it has started
        3) When the scan job completes, access the Report
        4) Check that the disabled facts are not present in the facts
           section of the report
    :expectedresults: The scan must completed without any error and a report
        should be available. The disabled products should not have results in
        the report.
    """
    errors_found = []
    disabled_facts = \
        QPC_EAP_RAW_FACTS + QPC_BRMS_RAW_FACTS + QPC_FUSE_RAW_FACTS
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name,
        'disabled-optional-products': 'jboss_fuse jboss_brms jboss_eap',
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({
        'id': scan_job_id,
    })
    assert result['status'] == 'completed'
    report_id = result['report_id']
    assert report_id is not None
    output_file = 'out.json'
    report = report_detail({
        'json': None,
        'output-file': output_file,
        'report': report_id,
    })
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get('sources')
        if sources:
            for source in sources:
                facts = source.get('facts')
                for fact in disabled_facts:
                    for dictionary in facts:
                        if fact in dictionary.keys():
                            errors_found.append(
                                'The fact {fact} should have '
                                'been DISABLED but was found '
                                'in report.'.format(
                                    fact=fact))

    assert len(errors_found) == 0, '\n================\n'.join(errors_found)


def test_scanjob_with_enabled_extended_products(isolated_filesystem,
                                                qpc_server_config):
    """Perform a scan with an optional products disabled.

    :id: 2294649e-3833-11e8-b467-0ed5f89f718b
    :description: Perform a a scan with optional products disabled and assert
        that the product facts are not collected in the report.
    :steps:
        1) Run ``qpc scan add --sources <source>
           --enabled-ext-product-search <optional-products>``
        2) Run ``qpc scan start --name scan``
        3) When the scan job completes, access the Report
        4) Check that the extended facts are present in the facts
           section of the report
    :expectedresults: The scan must completed without any error and a report
        should be available. The extended products should have results in
        the report.
    """
    errors_found = []
    extended_facts = \
        QPC_EAP_EXTENDED_FACTS + \
        QPC_BRMS_EXTENDED_FACTS + QPC_FUSE_EXTENDED_FACTS
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name,
        'enabled-ext-product-search': 'jboss_fuse jboss_brms jboss_eap',
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1200)
    result = scan_job({
        'id': scan_job_id,
    })
    assert result['status'] == 'completed'
    report_id = result['report_id']
    assert report_id is not None
    output_file = 'out.json'
    report = report_detail({
        'json': None,
        'output-file': output_file,
        'report': report_id,
    })
    with open(output_file) as report_data:
        report = json.load(report_data)
        sources = report.get('sources')
        if sources:
            for source in sources:
                facts = source.get('facts')
                for fact in extended_facts:
                    for dictionary in facts:
                        if fact not in dictionary.keys():
                            errors_found.append(
                                'The fact {fact} should have '
                                'been ENABLED but was not found '
                                'in report.'.format(
                                    fact=fact))

    assert len(errors_found) == 0, '\n================\n'.join(errors_found)


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
    scan_add_and_check({
        'name': scan_name,
        'sources': config_sources()[0]['name'],
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status='running')
    scan_pause({'id': scan_job_id})
    wait_for_scan(scan_job_id, status='paused')
    scan_restart({'id': scan_job_id})
    wait_for_scan(scan_job_id)
    result = scan_job({
        'id': scan_job_id,
    })
    assert result['status'] == 'completed'
    report_id = result['report_id']
    assert report_id is not None
    output_file = 'out.json'
    report = report_detail({
        'json': None,
        'output-file': output_file,
        'report': report_id,
    })
    with open(output_file) as report_data:
        report = json.load(report_data)
        assert report.get('sources', []) != []


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
    scan_add_and_check({
        'name': scan_name,
        'sources': config_sources()[0]['name'],
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status='running')
    scan_cancel({'id': scan_job_id})
    wait_for_scan(scan_job_id, status='canceled')
    result = scan_restart({'id': scan_job_id}, exitstatus=1)
    assert result.startswith(
        'Error: Scan cannot be restarted. The scan must be paused for it to '
        'be restarted.'
    )


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
    scan_add_and_check({
        'name': scan_name,
        'sources': config_sources()[0]['name'],
    })
    result = scan_start({
        'name': scan_name,
    })
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, status='running')
    scan_pause({'id': scan_job_id})
    wait_for_scan(scan_job_id, status='paused')
    scan_cancel({'id': scan_job_id})
    wait_for_scan(scan_job_id, status='canceled')
    result = scan_restart({'id': scan_job_id}, exitstatus=1)
    assert result.startswith(
        'Error: Scan cannot be restarted. The scan must be paused for it to '
        'be restarted.'
    )
