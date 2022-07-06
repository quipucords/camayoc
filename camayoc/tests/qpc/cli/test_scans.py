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

import pytest

from .utils import config_sources
from .utils import scan_add_and_check
from .utils import scan_clear
from .utils import scan_edit_and_check
from .utils import scan_show_and_check
from .utils import source_show
from camayoc.utils import client_cmd
from camayoc.utils import uuid4

NEGATIVE_CASES = [1, -100, "redhat_packages", "ifconfig", {}, [], ["/foo/bar/"]]


def test_create_scan(isolated_filesystem, qpc_server_config, source):
    """Create a single source scan.

    :id: 95d108dc-6a92-4723-aec2-10bc73a0e3fa
    :description: Create a single source scan with default options.
    :steps: Run ``qpc scan add --sources <source>``
    :expectedresults: The created scan matches default for options.
    """
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check({"name": scan_name, "sources": source_name})

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }

    scan_show_and_check(scan_name, expected_result)


def test_create_scan_with_options(isolated_filesystem, qpc_server_config, source):
    """Perform a scan and disable an optional product.

    :id: 79fadb3a-9e3c-4e84-890a-d2bd954c2869
    :description: Perform a scan and disable an optional product.
    :steps: Run ``qpc scan add --sources <source> --disable-optional-products
        <optional-product>``
    :expectedresults: The created scan matches specified options for options.
    """
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "max-concurrency": 25,
            "disabled-optional-products": "jboss_eap",
            "enabled-ext-product-search": "jboss_fuse",
        }
    )

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {
            "disabled_optional_products": {
                "jboss_brms": False,
                "jboss_eap": True,
                "jboss_fuse": False,
                "jboss_ws": False,
            },
            "enabled_extended_product_search": {
                "jboss_brms": False,
                "jboss_eap": False,
                "jboss_fuse": True,
                "jboss_ws": False,
            },
            "max_concurrency": 25,
        },
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }

    scan_show_and_check(scan_name, expected_result)


@pytest.mark.parametrize("fail_cases", NEGATIVE_CASES)
def test_create_scan_with_disabled_products_negative(
    isolated_filesystem, qpc_server_config, source, fail_cases
):
    """Attempt to create a scan with invalid values for disabled products.

    :id: 4acaaeb4-3833-11e8-b467-0ed5f89f718b
    :description: Create a scan with invalid values for disabled products.
    :steps:
        1) Call scan_add_and_check which runs the command
           ``qpc scan add --sources <source> --disabled-optional-products
           <optional-product>`` and asserts that it fails
    :expectedresults: The scan is not created
    """
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "disabled-optional-products": fail_cases,
        },
        r"usage: {} scan add(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )


@pytest.mark.parametrize("fail_cases", NEGATIVE_CASES)
def test_create_scan_with_extended_products_negative(
    isolated_filesystem, qpc_server_config, source, fail_cases
):
    """Attempt to create a scan with invalid values for extended products.

    :id: 190711ac-cde6-4a9f-bfbd-887c41094ed1
    :description: Create a scan with invalid values for extended products.
    :steps:
        1) Call scan_add_and_check which runs the command
           ``qpc scan add --sources <source> --enabled-ext-product-search
           <product>`` and asserts that it fails
    :expectedresults: The scan is not created
    """
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "enabled-ext-product-search": fail_cases,
        },
        r"usage: {} scan add(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )


@pytest.mark.parametrize("fail_cases", NEGATIVE_CASES)
def test_create_scan_with_extended_product_directories_negative(
    isolated_filesystem, qpc_server_config, source, fail_cases
):
    """Attempt to create a scan with invalid extended products directories.

    :id: 8461a2f5-f576-40fb-88b3-82109849e36c
    :description: Create a scan with invalid values for extended products.
    :steps:
        1) Call scan_add_and_check which runs the command
           ``qpc scan add --sources <source> --enabled-ext-product-search
           <product> --ext-product-search-dirs <directories>`` and asserts
           that it fails
    :expectedresults: The scan is not created
    """
    scan_name = uuid4()
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "enabled-ext-product-search": "jboss_fuse",
            "ext-product-search-dirs": fail_cases,
        },
        r"Error: {'enabled_extended_product_search': " r"{'search_directories'(.|[\r\n])*",
        exitstatus=1,
    )


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
    source_name = config_sources()[0]["name"]
    scan_add_and_check({"name": scan_name, "sources": source_name})

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }
    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check(
        {
            "name": scan_name,
            "max-concurrency": 25,
            "disabled-optional-products": "jboss_eap",
            "enabled-ext-product-search": "jboss_fuse",
            "ext-product-search-dirs": "/foo/bar/",
        },
        r'Scan "{}" was updated.'.format(scan_name),
    )

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {
            "disabled_optional_products": {
                "jboss_brms": False,
                "jboss_eap": True,
                "jboss_fuse": False,
                "jboss_ws": False,
            },
            "enabled_extended_product_search": {
                "jboss_brms": False,
                "jboss_eap": False,
                "jboss_fuse": True,
                "jboss_ws": False,
                "search_directories": ["/foo/bar/"],
            },
            "max_concurrency": 25,
        },
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }
    scan_show_and_check(scan_name, expected_result)


def test_edit_scan_with_options(isolated_filesystem, qpc_server_config, source):
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
    source_name = config_sources()[0]["name"]
    scan_add_and_check(
        {
            "name": scan_name,
            "sources": source_name,
            "max-concurrency": 25,
            "disabled-optional-products": "jboss_eap",
            "enabled-ext-product-search": "jboss_fuse",
        }
    )

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {
            "disabled_optional_products": {
                "jboss_brms": False,
                "jboss_eap": True,
                "jboss_fuse": False,
                "jboss_ws": False,
            },
            "enabled_extended_product_search": {
                "jboss_brms": False,
                "jboss_eap": False,
                "jboss_fuse": True,
                "jboss_ws": False,
            },
            "max_concurrency": 25,
        },
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }

    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check(
        {
            "name": scan_name,
            "max-concurrency": 25,
            "disabled-optional-products": "",
            "enabled-ext-product-search": "",
        },
        r'Scan "{}" was updated.'.format(scan_name),
    )

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {
            "disabled_optional_products": {
                "jboss_brms": False,
                "jboss_eap": False,
                "jboss_fuse": False,
                "jboss_ws": False,
            },
            "enabled_extended_product_search": {
                "jboss_brms": False,
                "jboss_eap": False,
                "jboss_fuse": False,
                "jboss_ws": False,
            },
            "max_concurrency": 25,
        },
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }
    scan_show_and_check(scan_name, expected_result)


def test_edit_scan_negative(isolated_filesystem, qpc_server_config, source):
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
    source_name = config_sources()[0]["name"]
    scan_add_and_check({"name": scan_name, "sources": source_name})

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }

    scan_show_and_check(scan_name, expected_result)

    # Edit scan options
    scan_edit_and_check(
        {"name": scan_name, "sources": ""},
        r"usage: {} scan edit(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )

    # Edit scan options
    scan_edit_and_check(
        {"name": scan_name, "sources": "fake_source"},
        r'Source "{}" does not exist.'.format("fake_source"),
        exitstatus=1,
    )

    # Edit scan options
    scan_edit_and_check(
        {"name": scan_name, "sources": source_name, "max-concurrency": "abc"},
        r"usage: {} scan edit(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )

    # Edit scan options
    scan_edit_and_check(
        {
            "name": scan_name,
            "sources": "",
            "disabled-optional-products": "not_a_real_product",
        },
        r"usage: {} scan edit(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )

    # Edit enabled-extended-product-search
    scan_edit_and_check(
        {
            "name": scan_name,
            "sources": "",
            "enabled-ext-product-search": "not_a_real_product",
        },
        r"usage: {} scan edit(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )

    # Edit ext-product-search-dirs
    scan_edit_and_check(
        {"name": scan_name, "sources": "", "ext-product-search-dirs": "not-a-dir"},
        r"usage: {} scan edit(.|[\r\n])*".format(client_cmd),
        exitstatus=2,
    )


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
    source_name = config_sources()[0]["name"]
    scan_add_and_check({"name": scan_name, "sources": source_name})

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }

    scan_show_and_check(scan_name, expected_result)

    # Remove scan
    result = scan_clear({"name": scan_name})
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
    source_name = config_sources()[0]["name"]
    scan_add_and_check({"name": scan_name, "sources": source_name})

    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "network"}],
    }
    scan_show_and_check(scan_name, expected_result)

    # Remove scan
    result = scan_clear({"all": None})
    match = re.match(r"All scans were removed.", result)
    assert match is not None
