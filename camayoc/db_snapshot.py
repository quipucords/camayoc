import dataclasses
import json
import logging
from operator import itemgetter
from pathlib import Path
from typing import Any

from camayoc.constants import DBSERIALIZER_CONNECTIONJOBS_DIR_PATH
from camayoc.constants import DBSERIALIZER_CREDENTIALS_FILE_PATH
from camayoc.constants import DBSERIALIZER_REPORTS_DIR_PATH
from camayoc.constants import DBSERIALIZER_SCANJOBS_DIR_PATH
from camayoc.constants import DBSERIALIZER_SCANS_FILE_PATH
from camayoc.constants import DBSERIALIZER_SOURCES_FILE_PATH

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class DBSnapshot:
    """DB Snapshot data representation suitable for test usage.

    The intended usage is through `from_dir()` constructor, which takes a path
    to snapshot data directory.

    DBSnapshot is responsible for transforming a data to a format suitable for
    native equality comparison. It means that lists may be reordered, fields
    with dynamic data can be removed etc.
    """

    credentials: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    scans: list[dict[str, Any]]
    connection_jobs: dict[str, Any]
    scan_jobs: dict[str, Any]
    reports: dict[str, Any]

    @classmethod
    def from_dir(cls, source: Path):
        credentials = read_credentials(source / DBSERIALIZER_CREDENTIALS_FILE_PATH)
        sources = read_sources(source / DBSERIALIZER_SOURCES_FILE_PATH)
        scans = read_scans(source / DBSERIALIZER_SCANS_FILE_PATH)
        connection_jobs = read_connection_jobs(source / DBSERIALIZER_CONNECTIONJOBS_DIR_PATH)
        scan_jobs = read_scan_jobs(source / DBSERIALIZER_SCANJOBS_DIR_PATH)
        reports = read_reports(source / DBSERIALIZER_REPORTS_DIR_PATH)
        return cls(credentials, sources, scans, connection_jobs, scan_jobs, reports)


def read_credentials(source: Path) -> list[dict[str, Any]]:
    with source.open() as fh:
        all_credentials = json.load(fh)
    return sorted(all_credentials, key=itemgetter("name"))


def read_sources(source: Path) -> list[dict[str, Any]]:
    with source.open() as fh:
        all_sources = json.load(fh)
    return sorted(all_sources, key=itemgetter("name"))


def read_scans(source: Path) -> list[dict[str, Any]]:
    with source.open() as fh:
        all_scans = json.load(fh)
    return sorted(all_scans, key=itemgetter("name"))


def read_connection_jobs(source: Path) -> dict[str, Any]:
    connection_jobs = {}

    for file in source.rglob("*"):
        if file.is_dir():
            continue
        key = file.stem
        with file.open() as fh:
            jobs = json.load(fh)
        connection_jobs[key] = sorted(jobs, key=_connection_job_itemgetter)

    return connection_jobs


def read_scan_jobs(source: Path) -> dict[str, Any]:
    scan_jobs = {}

    for file in source.rglob("*"):
        if file.is_dir():
            continue
        key = file.stem
        with file.open() as fh:
            jobs = json.load(fh)
        scan_jobs[key] = sorted(jobs, key=itemgetter("id"))

    return scan_jobs


def read_reports(source: Path) -> dict[str, Any]:
    all_reports = {}
    for directory in source.glob("*"):
        if directory.is_file():
            continue
        key = directory.name
        all_reports[key] = _read_report_directory(directory)
    return all_reports


def _read_report_directory(directory: Path):
    details_data = _read_report_details(next(directory.glob("details*.json")))
    aggregate_data = _read_report_aggregate(next(directory.glob("aggregate*.json")))
    return {
        "details": details_data,
        "aggregate": aggregate_data,
    }


def _read_report_details(file: Path):
    with file.open() as fh:
        data = json.load(fh)

    sources = data.get("sources", [])
    sources.sort(key=itemgetter("source_name"))

    for source in sources:
        source.get("facts", []).sort(key=_source_fact_itemgetter)

    return data


def _read_report_aggregate(file: Path):
    with file.open() as fh:
        data = json.load(fh)
    return data


def _connection_job_itemgetter(item):
    source_id = item.get("source", {}).get("id", 0)
    credential_id = item.get("credential", {}).get("id", 0)
    name = item.get("name", "")
    return f"{name}-{credential_id}-{source_id}"


def _source_fact_itemgetter(item):
    vm_uuid = item.get("vm.uuid", "")
    vm_host_uuid = item.get("vm.host.uuid", "")
    if vm_uuid or vm_host_uuid:
        return f"{vm_uuid}-{vm_host_uuid}"

    hostname = item.get("hostname")
    organization = item.get("organization")
    location = item.get("location")
    if hostname and organization and location:
        return f"{organization}-{location}-{hostname}"

    etc_id = item.get("etc_machine_id", "")
    subman_id = item.get("subscription_manager_id", "")
    dmi_uuid = item.get("dmi_system_uuid", "")
    return f"{etc_id}-{subman_id}-{dmi_uuid}"
