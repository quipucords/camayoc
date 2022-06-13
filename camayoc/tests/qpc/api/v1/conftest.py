"""Pytest customizations and fixtures for the quipucords tests."""
from pprint import pformat

import pytest

import requests

from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError, WaitTimeError
from camayoc.qpc_models import Credential, Scan, ScanJob, Source
from camayoc.tests.qpc.api.v1.utils import wait_until_state
from camayoc.tests.utils import get_vcenter_vms, vcenter_vms
from camayoc.utils import run_scans


SCAN_DATA = {}
"""Cache to associate the named scans with their results."""


def create_cred(cred_info, cleanup):
    """Given info about cred from config file, create it and return id."""
    c = Credential(**cred_info)
    c.create()
    cleanup.append(c)
    return c._id


def create_source(source_info, cleanup):
    """Given info about source from config file, create it and return id."""
    src = Source(**source_info)
    src.create()
    cleanup.append(src)
    return src._id


def run_scan(
    scan,
    disabled_optional_products,
    enabled_extended_product_search,
    cleanup,
    scan_type="inspect",
):
    """Scan a machine and cache any available results.

    If errors are encountered, save those and they can be included
    in test results.
    """
    src_ids = scan["source_ids"]
    scan_name = scan["name"]
    SCAN_DATA[scan_name] = {
        "scan_id": None,  # scan id
        "scan_job_id": None,  # scan job id
        "final_status": None,  # Did the scan job contain any failed tasks?
        "scan_results": None,  # Number of systems reached, etc
        "report_id": None,  # so we can retrieve report
        "connection_results": None,  # details about connection scan
        "inspection_results": None,  # details about inspection scan
        "errors": [],
        "expected_products": scan["expected_products"],
        "source_id_to_hostname": scan["source_id_to_hostname"],
    }
    try:
        scan = Scan(
            source_ids=src_ids,
            scan_type=scan_type,
            disabled_optional_products=disabled_optional_products,
            enabled_extended_product_search=enabled_extended_product_search,
        )
        scan.create()
        cleanup.append(scan)
        scanjob = ScanJob(scan_id=scan._id)
        scanjob.create()
        SCAN_DATA[scan_name]["scan_id"] = scan._id
        SCAN_DATA[scan_name]["scan_job_id"] = scanjob._id
        wait_until_state(scanjob, state="stopped")
        SCAN_DATA[scan_name]["final_status"] = scanjob.status()
        SCAN_DATA[scan_name]["scan_results"] = scanjob.read().json()
        SCAN_DATA[scan_name]["report_id"] = scanjob.read().json().get("report_id")
        if scan_type == "inspect":
            SCAN_DATA[scan_name]["task_results"] = scanjob.read().json().get("tasks")
            SCAN_DATA[scan_name]["inspection_results"] = (
                scanjob.inspection_results().json().get("results")
            )
    except (requests.HTTPError, WaitTimeError) as e:
        SCAN_DATA[scan_name]["errors"].append("{}".format(pformat(str(e))))


@pytest.fixture(scope="session", autouse=run_scans())
def run_all_scans(vcenter_client):
    """Run all configured scans caching the report id associated with each.

    Run each scan defined in the ``qpc`` section of the configuration file.

    Cache the report id of the scan, associating it with its scan.

    The expected configuration in the Camayoc's configuration file is as
    follows::

        qpc:
        # other needed qpc config data
        #
        # specific for scans:
            - scans:
                - name: network-vcenter-sat-mix
                  sources:
                      - sample-none-rhel-5-vc
                      - sample-sat-6
                      - sample-vcenter
                  disabled_optional_products: {'jboss_fuse': True}
                  type: 'connect'
                  enabled_extended_product_search: {'jboss_eap': True,
                     'search_directories': ['/foo/bar']}
        inventory:
          - hostname: sample-none-rhel-5-vc
            ipv4: 10.10.10.1
            hypervisor: vcenter
            distribution:
                name: rhel
                version: '5.9'
            products: {}
            credentials:
                - root
          - hostname: sample-sat-6
            type: 'vcenter'
            options:
                ssl_cert_verify: false
            credentials:
                - sat6_admin
          - hostname: sample-vcenter
            type: 'vcenter'
            credentials:
                - vcenter_admin

        credentials:
            - name: root
              sshkeyfile: /path/to/.ssh/id_rsa
              username: root
              type: network

            - name: sat6_admin
              password: foo
              username: admin
              type: satellite

            - name: vcenter_admin
              password: foo
              username: admin
              type: vcenter

    In the sample configuration file above, one machine will be turned on,
    and one scan will be run against the three sources each created with
    their own credential.
    """
    cleanup = []
    config = get_config()

    config_scans = config.get("qpc", {}).get("scans", [])
    if not config_scans:
        # if no scans are defined, no need to go any further
        return

    config_creds = {
        credential["name"]: credential for credential in config.get("credentials", [])
    }
    inventory = {machine["hostname"]: machine for machine in config["inventory"]}
    vcenter_inventory = {
        machine["hostname"]: machine
        for machine in config["inventory"]
        if machine.get("hypervisor") == "vcenter"
    }

    if not config_creds or not inventory:
        raise ValueError(
            "Make sure to have credentials and inventory" " items in the config file"
        )

    credential_ids = {}
    source_ids = {}
    expected_products = {}
    for scan in config_scans:
        scan_vms = {
            vm.name: vm
            for vm in get_vcenter_vms(vcenter_client)
            if (vm.name in vcenter_inventory) and (vm.name in scan["sources"])
        }

        with vcenter_vms(scan_vms.values()):
            for source_name in scan["sources"]:
                if source_name not in source_ids:
                    machine = inventory[source_name]
                    for credential_name in machine["credentials"]:
                        if credential_name not in credential_ids:
                            credential = config_creds[credential_name].copy()
                            credential["cred_type"] = credential.pop("type")
                            credential["ssh_keyfile"] = credential.pop(
                                "sshkeyfile", None
                            )
                            credential_ids[credential_name] = create_cred(
                                credential, cleanup
                            )
                    if machine.get("type", "network") == "network":
                        vm = scan_vms[machine["hostname"]]
                        machine["ipv4"] = vm.guest.ipAddress
                    source_info = {
                        "source_type": machine.get("type", "network"),
                        "hosts": [machine.get("ipv4") or machine["hostname"]],
                        "credential_ids": [
                            credential_ids[credential]
                            for credential in machine["credentials"]
                        ],
                    }
                    if "options" in machine:
                        source_info["options"] = machine["options"].copy()
                    source_ids[source_name] = create_source(source_info, cleanup)
                    expected_products[source_name] = machine.get("products", {})
                    expected_products[source_name].update(
                        {"distribution": source_info.get("distribution", {})}
                    )

            scan_info = {
                "expected_products": [],
                "name": scan["name"],
                "source_id_to_hostname": {},
                "source_ids": [],
            }
            for source_name in scan["sources"]:
                source_id = source_ids[source_name]
                scan_info["expected_products"].append(
                    {source_id: expected_products[source_name]}
                )
                scan_info["source_id_to_hostname"][source_id] = source_name
                scan_info["source_ids"].append(source_id)

            run_scan(
                scan_info,
                scan.get("disabled_optional_products", {}),
                scan.get("enabled_extended_product_search", {}),
                cleanup=cleanup,
                scan_type=scan.get("type", "inspect"),
            )


def scan_list():
    """Generate list of scan dict objects found in config file."""
    try:
        return get_config().get("qpc", {}).get("scans", [])
    except (ConfigFileNotFoundError, KeyError):
        return []


def get_scan_result(scan_name):
    """Collect scan results from global cache.

    Raise an error if no results are available, because this means the scan
    was not even attempted.
    """
    result = SCAN_DATA.get(scan_name)
    if result is None:
        raise RuntimeError(
            "Absolutely no results available for scan named {0},\n"
            "because no scan was even attempted.\n".format(scan_name)
        )
    return result
