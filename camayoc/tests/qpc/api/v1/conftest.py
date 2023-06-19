"""Pytest customizations and fixtures for the quipucords tests."""
from pprint import pformat

import requests

from camayoc.config import settings
from camayoc.exceptions import WaitTimeError
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import ScanJob
from camayoc.qpc_models import Source
from camayoc.tests.qpc.api.v1.utils import wait_until_state

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

    This is dead code. It is left around as a visible reference of data
    structure that has been used. It might serve as inspiration for better
    solution in the future.
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


def scan_list():
    """Generate list of netwok / VCenter / Satellite scan objects found in config file."""
    scans = []
    supported_source_types = ("network", "vcenter", "satellite")
    source_names_types = {s.name: s.type for s in settings.sources}
    for scan in settings.scans:
        source_types = [source_names_types.get(source) for source in scan.sources]
        if not all(source_type in supported_source_types for source_type in source_types):
            continue
        scans.append(scan)
    return scans
