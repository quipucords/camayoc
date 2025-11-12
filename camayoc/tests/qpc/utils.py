"""Utility functions for quipucords server tests."""

import hashlib
import json
import pprint
import tarfile
import time
from pathlib import Path
from typing import Callable

import pytest

from camayoc import api
from camayoc.config import settings
from camayoc.constants import QPC_SCAN_STATES
from camayoc.constants import QPC_SCAN_TERMINAL_STATES
from camayoc.constants import SOURCE_TYPES_WITH_LIGHTSPEED_SUPPORT
from camayoc.exceptions import StoppedScanException
from camayoc.exceptions import WaitTimeError
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import Source
from camayoc.types.scans import FinishedScan
from camayoc.types.settings import ScanOptions


def calculate_sha256sums(directory):
    """Calculate SHA256 sum of all files in directory."""
    directory = Path(directory)
    shasums = {}
    for file in directory.rglob("*"):
        if not file.is_file():
            continue
        key = str(file.relative_to(directory))
        shasum = hashlib.sha256()
        with open(file, "rb") as fh:
            while block := fh.read(4096):
                shasum.update(block)
        shasums[key] = shasum.hexdigest()
    return shasums


def get_expected_sha256sums(directory):
    """Find SHA256SUM files in directory and parse them.

    SHA256SUM file names are transformed to be relative to directory arg,
    so output of this function should be strict subset of output of
    `calculate_sha256sums` ran on the same directory.
    """
    directory = Path(directory)
    parsed_shasums = {}
    for file in directory.rglob("*"):
        if file.name != "SHA256SUM":
            continue

        with open(file) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                expected_sum, filename = line.split(maxsplit=1)
                if not filename:
                    continue
                key = str(file.relative_to(directory).with_name(filename))
                parsed_shasums[key] = expected_sum

    return parsed_shasums


def assert_sha256sums(directory: Path):
    """Verify SHA256 sums of files match. Tests helper."""
    actual_shasums = calculate_sha256sums(directory)
    expected_shasums = get_expected_sha256sums(directory)

    for filename, expected_shasum in expected_shasums.items():
        actual_shasum = actual_shasums.get(filename)
        assert actual_shasum == expected_shasum


def assert_ansible_logs(directory: Path, is_network_scan: bool):
    """Verify that ansible log files exist (or not). Tests helper."""
    has_ansible_logs = False
    for file in directory.rglob("*"):
        if not file.is_file():
            continue

        # Ansible STDERR may or may not be empty, no point in asserting size
        if "ansible-stderr" in file.name:
            has_ansible_logs = True
            continue

        if "ansible-stdout" in file.name:
            has_ansible_logs = True

        assert file.stat().st_size > 0

    assert is_network_scan == has_ansible_logs


def assert_lightspeed_report(directory: Path, expect_lightspeed_report: bool):
    """Verify that lightspeed report exists (or not), and verify the content. Tests helper."""
    for file in directory.rglob("*"):
        if not file.is_file():
            continue
        if file.name.endswith("tar.gz") and "lightspeed" in file.name:
            lightspeed_report_path = file.resolve()
            break
    # This block is executed only if there is no lightspeed report. We assert this is what
    # caller wanted and exit early, as rest of the function focuses on report content.
    else:
        assert expect_lightspeed_report == False, (
            "Lightspeed report tarball not found, caller expected it"
        )
        return

    assert expect_lightspeed_report == True, "Unexpected Lightspeed report tarball found"
    assert lightspeed_report_path.stat().st_size > 0

    tar = tarfile.open(lightspeed_report_path)
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
    assert tar_content["metadata.json"].get("report_slices", {}) == tar_content["report_slices"], (
        "Data in metadata.json and actual data in archive do not match"
    )


def scan_should_have_lightspeed_report(finished_scan: FinishedScan) -> bool:
    """Check if this scan should have lightspeed report or not."""
    source_name_type_map = {source.name: source.type for source in settings.sources}
    scan_source_types = {
        source_name_type_map.get(source) for source in finished_scan.definition.sources
    }
    return bool(scan_source_types.intersection(SOURCE_TYPES_WITH_LIGHTSPEED_SUPPORT))


def get_object_id(obj):
    """Get id of object whose name is known."""
    if obj._id:
        return obj._id

    available_objs = obj.list(params={"search_by_name": obj.name}).json()
    for received_obj in available_objs.get("results", []):
        if received_obj.get("name") == obj.name:
            return received_obj.get("id")


def sort_and_delete(trash):
    """Sort and delete a list of QPCObject typed items in the correct order."""
    creds = []
    sources = []
    scans = []

    client = api.Client(response_handler=api.echo_handler)
    # first sort into types because we have to delete scans before sources
    # and sources before scans
    for obj in trash:
        # Override client to use a fresh one. It may have been a while
        # since the object was created and its token may be invalid.
        obj.client = client
        # Get object id based on the name.
        # This allows us to clean up objects created from UI and CLI.
        # If object id could not be found, assume object was already deleted.
        if not obj._id and obj.name:
            obj._id = get_object_id(obj)
        if obj._id is None:
            continue

        if isinstance(obj, Credential):
            creds.append(obj)
        elif isinstance(obj, Source):
            sources.append(obj)
        elif isinstance(obj, Scan):
            scans.append(obj)

    for collection in (scans, sources, creds):
        if not collection:
            continue

        ids = [obj._id for obj in collection]
        obj = collection[0]
        # Only assert that we do not hit an internal server error
        response = obj.bulk_delete(ids=ids)
        assert response.status_code < 500, response.content


def all_source_names() -> list[str]:
    """Grab a list of all source names."""
    matching_sources = [source_definition.name for source_definition in settings.sources]
    return matching_sources


def all_scan_names() -> list[str]:
    """Grab a list of all scan names."""
    matching_scans = [scan_definition.name for scan_definition in settings.scans]
    return matching_scans


def scan_names(predicate: Callable[[ScanOptions], bool]) -> list[str]:
    """Grab a list of scan names for which predicate returns True."""
    matching_scans = [
        scan_definition.name for scan_definition in settings.scans if predicate(scan_definition)
    ]
    return matching_scans


def end_to_end_sources_names():
    """Generate source names as pytest params.

    This is used by CLI and UI end_to_end tests.
    """
    for source_definition in settings.sources:
        if source_definition.type in ("openshift", "rhacs"):
            continue
        fixture_id = f"{source_definition.name}-{source_definition.type}"
        yield pytest.param(source_definition.name, id=fixture_id)


def wait_until_state(scanjob, timeout=settings.camayoc.scan_timeout, state="completed"):
    """Wait until the scanjob has failed or reached desired state.

    The default state is 'completed'.

    Valid options for 'state': 'completed', 'failed', 'canceled',
    'running', 'stopped'.

    If 'stopped' is selected, then any state other than 'running' will
    cause `wait_until_state` to return.

    This method should not be called on scanjob jobs that have not yet been
    created or are canceled.

    The default timeout is specified by scan_timeout setting, which
    currently is set to 600 seconds (10 minutes). In the past it was
    an hour. Hour was used because it has been proven that in general
    the server is accurate when reporting that a task really is still
    running. Data from pipeline runs in 2024 indicates that standard
    scan in our environment takes no more than 5 minutes to complete.

    All other terminal states will cause this function to return before
    reaching the timeout.
    """
    valid_states = QPC_SCAN_STATES + ("stopped",)
    stopped_states = QPC_SCAN_TERMINAL_STATES + ("stopped",)
    if state not in valid_states:
        raise ValueError(
            "You have called `wait_until_state` and specified an invalid\n"
            'state={0}. Valid options for "state" are [ {1} ]'.format(
                state, pprint.pformat(valid_states)
            )
        )

    current_status = scanjob.status()
    while True:
        # achieved expected state - happy path
        if current_status == state:
            return

        # scanjob is no longer running, user wanted one of stopped states. Stopped is stopped
        if current_status in stopped_states and state in stopped_states:
            return

        scanjob_details = scanjob.read().json()
        exception_format = {
            "scanjob_id": scanjob._id,
            "scan_id": scanjob.scan_id,
            "expected_state": state,
            "scanjob_state": current_status,
            "scanjob_details": pprint.pformat(scanjob_details),
            "scanjob_results": pprint.pformat(scanjob_details.get("tasks")),
        }

        if current_status in stopped_states and state not in stopped_states:
            raise StoppedScanException(
                "You have called wait_until_state() on a scanjob with\n"
                "ID={scanjob_id} has stopped running instead of reaching \n"
                'the state="{expected_state}"\n'
                'When the scanjob stopped, it had the state="{scanjob_state}".'
                "\nThe scanjob was started for the scan with id {scan_id}"
                "The full details of the scanjob were \n{scanjob_details}\n"
                'The "results" available from the scanjob were \n'
                "{scanjob_results}\n".format(**exception_format)
            )

        if timeout <= 0:
            raise WaitTimeError(
                "You have called wait_until_state() on a scanjob with\n"
                "ID={scanjob_id} and the scanjob timed out while waiting\n"
                'to achieve the state="{expected_state}"\n'
                "When the scanjob timed out, it had the"
                ' state="{scanjob_state}".\n'
                "The scanjob was started for the scan with id {scan_id}"
                "The full details of the scanjob were \n{scanjob_details}\n"
                'The "results" available from the scanjob were'
                "\n{scanjob_results}\n".format(**exception_format)
            )

        time.sleep(5)
        timeout -= 5
        current_status = scanjob.status()
