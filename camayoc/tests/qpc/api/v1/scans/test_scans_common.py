# coding=utf-8
"""Tests for ``Scan`` API endpoint for quipucords server.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:testtype: functional
"""
import random
from itertools import combinations

import pytest

from camayoc import api
from camayoc.constants import QPC_OPTIONAL_PRODUCTS
from camayoc.constants import QPC_SOURCE_TYPES
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.utils import gen_valid_source
from camayoc.utils import uuid4

OPTIONAL_PROD = "disabled_optional_products"
"""The key in the json request to enable/disable optional products."""


@pytest.mark.parametrize("scan_type", ["connect", "inspect"])
def test_create(shared_client, cleanup, scan_type):
    """Create scan and assert it has correct values.

    :id: ee3b0bc8-1489-443e-86bb-e2a2349e9c98
    :description: Create a scan and assert that it completes
    :steps:
        1) Create a network credential
        2) Create a network source with the credential
        3) Create a scan with the network source
        4) Assert that the scan is created and all fields match the request.
    :expectedresults: A scan is created with all options set as requested.
    """
    source_ids = []
    for _ in range(random.randint(1, 10)):
        src_type = random.choice(QPC_SOURCE_TYPES)
        src = gen_valid_source(cleanup, src_type, "localhost")
        source_ids.append(src._id)
    scan = Scan(source_ids=source_ids, scan_type=scan_type, client=shared_client)
    scan.create()
    cleanup.append(scan)
    remote_scn = scan.read().json()
    assert scan.equivalent(remote_scn)


@pytest.mark.parametrize("update_field", ["name", "max_concurrency", "source"])
@pytest.mark.parametrize("scan_type", ["connect", "inspect"])
def test_update(update_field, shared_client, cleanup, scan_type):
    """Create scan, then update it and assert the values are changed.

    :id: c40a64c1-346e-4fce-ad18-4090066050a1
    :description: Create a scan and assert that it completes
    :steps:
        1) Create a network credential
        2) Create a network source with the credential
        3) Create a scan with the network source
        4) Assert that the scan is created and all fields match the request.
        5) Update a field and assert that changes are made
    :expectedresults: A scan is created with all options set as requested.
    """
    source_ids = []
    for _ in range(random.randint(1, 10)):
        src_type = random.choice(QPC_SOURCE_TYPES)
        src = gen_valid_source(cleanup, src_type, "localhost")
        source_ids.append(src._id)
    scan = Scan(source_ids=source_ids, scan_type=scan_type, client=shared_client)
    scan.create()
    cleanup.append(scan)
    remote_scn = scan.read().json()
    assert scan.equivalent(remote_scn)
    if update_field == "source":
        src_type = random.choice(QPC_SOURCE_TYPES)
        src = gen_valid_source(cleanup, src_type, "localhost")
        scan.sources.append(src._id)
    if update_field == "max_concurrency":
        scan.options.update({"max_concurrecny": random.randint(1, 49)})
    if update_field == "name":
        scan.name = uuid4()
    scan.update()
    remote_scn = scan.read().json()
    assert scan.equivalent(remote_scn)


@pytest.mark.parametrize("scan_type", ["connect", "inspect"])
def test_scan_with_optional_products(scan_type, shared_client, cleanup):
    """Create a scan with disabled optional products.

    :id: 366604ed-e423-4140-b0d8-38626e264688
    :description: Perform a scan and disable an optional product.
    :steps:
        1) Create a network credential
        2) Create network source using the network credential.
        3) Create a scan using the network source. When creating the scan
           disable the optional products.
    :expectedresults: The scan is created.
    """
    num_products = random.randint(0, len(QPC_OPTIONAL_PRODUCTS))
    product_combinations = combinations(QPC_OPTIONAL_PRODUCTS, num_products)
    for combo in product_combinations:
        source_ids = []
        for _ in range(random.randint(1, 10)):
            src_type = random.choice(QPC_SOURCE_TYPES)
            src = gen_valid_source(cleanup, src_type, "localhost")
            source_ids.append(src._id)
        scan = Scan(source_ids=source_ids, scan_type=scan_type, client=shared_client)
        products = {p: True for p in QPC_OPTIONAL_PRODUCTS if p not in combo}
        products.update({p: False for p in combo})
        scan.options.update({OPTIONAL_PROD: products})
        scan.create()
        cleanup.append(scan)
        assert scan.equivalent(scan.read().json())


@pytest.mark.parametrize("scan_type", ["connect", "inspect"])
def test_negative_disable_optional_products(scan_type, shared_client, cleanup):
    """Attempt to disable optional products with non-acceptable booleans.

    :id: 2adb483c-578d-4131-b426-9f772c1803de
    :description: Create a scan with bad input for optional products
    :steps:
        1) Create a network credential
        2) Create network source using the network credential.
        3) Create a scan using the network source. When creating the scan
           disable the optional products with bad values.
    :expectedresults: The scan is not created.
    """
    num_products = random.randint(1, len(QPC_OPTIONAL_PRODUCTS))
    product_combinations = combinations(QPC_OPTIONAL_PRODUCTS, num_products)
    for combo in product_combinations:
        source_ids = []
        for _ in range(random.randint(1, 10)):
            src_type = random.choice(QPC_SOURCE_TYPES)
            src = gen_valid_source(cleanup, src_type, "localhost")
            source_ids.append(src._id)
        scan = Scan(source_ids=source_ids, scan_type=scan_type, client=shared_client)
        products = {p: True for p in QPC_OPTIONAL_PRODUCTS if p not in combo}
        bad_choice = random.choice(["hamburger", "87", 42, "*"])
        products.update({p: bad_choice for p in combo})
        scan.options.update({OPTIONAL_PROD: products})
        echo_client = api.Client(response_handler=api.echo_handler)
        scan.client = echo_client
        create_response = scan.create()
        if create_response.status_code == 201:
            cleanup.append(scan)
            raise AssertionError(
                "Optional products should be disabled and\n"
                "enabled with booleans. If invalid input is given, the user\n"
                "should be alerted."
                "The following data was provided: {}".format(products)
            )
        assert create_response.status_code == 400
        message = create_response.json().get("options", {})
        assert message.get(OPTIONAL_PROD) is not None
