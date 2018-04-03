# coding=utf-8
"""Tests for ``qpc scan`` configuration commands.

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

import pexpect

import pytest

from camayoc.config import get_config
from camayoc.constants import BECOME_PASSWORD_INPUT, CONNECTION_PASSWORD_INPUT
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.utils import name_getter, uuid4

from .conftest import qpc_server_config
from .utils import (
    cred_add,
    scan_add_and_check,
    scan_clear,
    scan_edit_and_check,
    scan_show_and_check,
    source_add,
    source_show_output
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
def setup():
    """Create all credentials and sources on the server."""
    qpc_server_config()

    # Delete artifacts in reverse order to avoid 400 errors
    qpc_clear = pexpect.spawn(
        'qpc scan clear --all'
    )
    assert qpc_clear.expect(pexpect.EOF) == 0
    qpc_clear.close()

    qpc_clear = pexpect.spawn(
        'qpc source clear --all'
    )
    assert qpc_clear.expect(pexpect.EOF) == 0
    qpc_clear.close()

    qpc_clear = pexpect.spawn(
        'qpc cred clear --all'
    )
    assert qpc_clear.expect(pexpect.EOF) == 0
    qpc_clear.close()

    # Create new creds
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
        cred_add(credential, inputs)

    # create sources
    sources = get_config().get('qpc', {}).get('sources', [])
    for source in sources:
        source['cred'] = source.pop('credentials')
        options = source.pop('options', {})
        for k, v in options.items():
            source[k.replace('_', '-')] = v
        source_add(source)


@pytest.mark.troubleshoot
def test_create_scan(isolated_filesystem, qpc_server_config, source):
    """Create a single source scan.

    :id: 95d108dc-6a92-4723-aec2-10bc73a0e3fa
    :description: Create a single source scan with default options.
    :steps: Run ``qpc scan add --sources <source>``
    :expectedresults: The created scan matches default for options.
    """
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}

    scan_show_and_check(scan_name, expected_result)


def test_create_scan_with_options(isolated_filesystem,
                                  qpc_server_config, source):
    """Perform a scan and disable an optional product.

    :id: 79fadb3a-9e3c-4e84-890a-d2bd954c2869
    :description: Perform a scan and disable an optional product.
    :steps: Run ``qpc scan add --sources <source> --disable-optional-products
        <optional-product>``
    :expectedresults: The created scan matches specified options for options.
    """
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name,
        'max-concurrency': 25,
        'disabled-optional-products': 'jboss_eap',
        'enabled-ext-product-search': 'jboss_fuse'
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'disabled_optional_products': {
                               'jboss_brms': False,
                               'jboss_eap': True,
                               'jboss_fuse': False},
                           'enabled_extended_product_search': {
                               'jboss_brms': False,
                               'jboss_eap': False,
                               'jboss_fuse': True},
                           'max_concurrency': 25},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}

    scan_show_and_check(scan_name, expected_result)


def test_edit_scan(isolated_filesystem, qpc_server_config, source):
    """Edit a single source scan.

    :id: 5ad22515-2276-48b5-a896-f26f039134fa
    :description: Create a single source scan with default options
        then edit to use non-default options.
    :steps:
        1) Run ``qpc scan add --sources <source>``
        2) Run ``qpc scan edit --name <name> --disable-optional-products <optional-product>`` # noqa
    :expectedresults: The edited scan matches specified options for options.
    """
    # Create scan
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}
    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'max-concurrency': 25,
        'disabled-optional-products': 'jboss_eap',
        'enabled-ext-product-search': 'jboss_fuse'
    }, r'Scan "{}" was updated.'.format(scan_name))

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'disabled_optional_products': {
                               'jboss_brms': False,
                               'jboss_eap': True,
                               'jboss_fuse': False},
                           'enabled_extended_product_search': {
                               'jboss_brms': False,
                               'jboss_eap': False,
                               'jboss_fuse': True},
                           'max_concurrency': 25},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}
    scan_show_and_check(scan_name, expected_result)


def test_edit_scan_with_options(isolated_filesystem,
                                qpc_server_config, source):
    """Perform a scan and disable an optional product.

    :id: 29e36e96-3682-11e8-b467-0ed5f89f718b
    :description: Perform a scan and disable an optional product.
    :steps:
        1) Run ``qpc scan add --sources <source> --disable-optional-products
        <optional-product>``
        2) Run ``qpc scan edit --name <name>``
    :expectedresults: The edited scan matches default.
    """
    # Create scan
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name,
        'max-concurrency': 25,
        'disabled-optional-products': 'jboss_eap',
        'enabled-ext-product-search': 'jboss_fuse'
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'disabled_optional_products': {
                               'jboss_brms': False,
                               'jboss_eap': True,
                               'jboss_fuse': False},
                           'enabled_extended_product_search': {
                               'jboss_brms': False,
                               'jboss_eap': False,
                               'jboss_fuse': True},
                           'max_concurrency': 25},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}

    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'max-concurrency': 50,
        'disabled-optional-products': '',
        'enabled-ext-product-search': ''
    }, r'Scan "{}" was updated.'.format(scan_name))

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'disabled_optional_products': {
                               'jboss_brms': False,
                               'jboss_eap': False,
                               'jboss_fuse': False},
                           'enabled_extended_product_search': {
                               'jboss_brms': False,
                               'jboss_eap': False,
                               'jboss_fuse': False},
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}
    scan_show_and_check(scan_name, expected_result)


def test_edit_scan_negative(isolated_filesystem,
                            qpc_server_config, source):
    """Create a single source  scan.

    :id: 29e37242-3682-11e8-b467-0ed5f89f718b
    :description: Attempt to rename scan to match another existing
        scan name.
    :steps:
        1) Run ``qpc scan add --sources <source>``
        2) Run ``qpc scan edit --name``
    :expectedresults: Scan edit fails due to invalid options.
    """
    # Create scan
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}

    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'sources': ''
    }, r'usage: qpc scan edit(.|[\r\n])*', exitstatus=2)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'sources': 'fake_source'
    }, r'Source "{}" does not exist.'.format('fake_source'),
        exitstatus=1)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'sources': source_name,
        'max-concurrency': 'abc'
    }, r'usage: qpc scan edit(.|[\r\n])*', exitstatus=2)

    # Edit scan options
    scan_edit_and_check({
        'name': scan_name,
        'sources': '',
        'disabled-optional-products': 'not_a_real_product',

    }, r'usage: qpc scan edit(.|[\r\n])*', exitstatus=2)


def test_clear(isolated_filesystem, qpc_server_config, source):
    """Create a single source  scan.

    :id: 29e3744a-3682-11e8-b467-0ed5f89f718b
    :description: Create a single source scan with default options
         and delete it.
    :steps:
        1) Run ``qpc scan add --sources <source>``
        2) Run ``qpc scan clear --name <name>``
    :expectedresults: Scan is deleted.
    """
    # Create scan
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}

    scan_show_and_check(scan_name, expected_result)

    # Remove scan
    result = scan_clear({
        'name': scan_name
    })
    match = re.match(r'Scan "{}" was removed.'.format(scan_name), result)
    assert match is not None


def test_clear_all(isolated_filesystem, qpc_server_config, scan_type):
    """Clear all sources.

    :id: 29e37620-3682-11e8-b467-0ed5f89f718b
    :description: Clear multiple scan entries using the ``--all`` option.
    :steps:
        1) Run ``qpc scan add --sources <source>``
        2) Run ``qpc scan add --sources <source>``
        3) Run ``qpc source clear --all``
    :expectedresults: All scans entries are removed.
    """
    # Create scan
    scan_name = uuid4()
    source_name = config_sources()[0]['name']
    scan_add_and_check({
        'name': scan_name,
        'sources': source_name
    })

    source_output = source_show_output({'name': source_name})
    source_output = json.loads(source_output)

    expected_result = {'id': 'TO_BE_REPLACED',
                       'name': scan_name,
                       'options': {
                           'max_concurrency': 50},
                       'scan_type': 'inspect',
                       'sources': [{'id': source_output['id'],
                                    'name': source_name,
                                    'source_type': 'network'}]}
    scan_show_and_check(scan_name, expected_result)

    # Remove scan
    result = scan_clear({
        'all': None
    })
    match = re.match(r'All scans were removed.', result)
    assert match is not None
