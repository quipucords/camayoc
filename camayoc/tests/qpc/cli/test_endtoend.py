import random
import re
import tarfile

import pytest

from camayoc.config import settings
from camayoc.constants import CONNECTION_PASSWORD_INPUT
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.utils import assert_ansible_logs
from camayoc.tests.qpc.utils import assert_sha256sums
from camayoc.tests.qpc.utils import end_to_end_sources_names
from camayoc.utils import uuid4

from .utils import cred_add_and_check
from .utils import report_download
from .utils import scan_add_and_check
from .utils import scan_job
from .utils import scan_start
from .utils import source_add_and_check
from .utils import wait_for_scan


@pytest.mark.slow
@pytest.mark.nightly_only
@pytest.mark.parametrize("source_name", end_to_end_sources_names())
def test_end_to_end(tmp_path, qpc_server_config, data_provider, source_name):
    """End-to-end test using command line interface.

    :id: 5649c69b-1e14-4279-b571-5aec12ea0716
    :description: This is end-to-end user journey through command line interface.
    :steps:
        1) Create new credential.
        2) Create new source.
        3) Trigger scan for newly created source.
        4) Wait for scan to complete.
        5) Download scan report.
    :expectedresults: Credential and Source are created. Scan is completed.
        Report is downloaded.
    """
    scan_name = uuid4()

    # Get a random credential associated with a source in configuration
    known_sources_map = {
        source_definition.name: source_definition for source_definition in settings.sources
    }
    source_definition = known_sources_map.get(source_name)
    credential_name = random.choice(source_definition.credentials)
    credential_model = data_provider.credentials.new_one({"name": credential_name}, data_only=True)
    data_provider.mark_for_cleanup(credential_model)

    # Create a credential
    cred_add_args = {
        "name": credential_model.name,
        "username": credential_model.username,
        "type": credential_model.cred_type,
    }
    secret_inputs = []
    if cred_password := credential_model.password:
        secret_inputs.append((CONNECTION_PASSWORD_INPUT, cred_password))
        cred_add_args["password"] = None
    if cred_ssh_key := credential_model.ssh_key:
        secret_inputs.append(("Private SSH Key:", cred_ssh_key))
        cred_add_args["sshkey"] = None
    cred_add_and_check(cred_add_args, inputs=secret_inputs)

    # Create a source
    source_model = data_provider.sources.new_one(
        {"name": source_definition.name}, new_dependencies=True, data_only=True
    )
    source_add_args = {
        "name": source_model.name,
        "cred": [credential_model.name],
        "hosts": source_model.hosts,
        "type": source_model.source_type,
    }
    if source_port := getattr(source_model, "port", None):
        source_add_args["port"] = source_port
    if source_options := getattr(source_model, "options", {}):
        source_add_args.update({key.replace("_", "-"): val for key, val in source_options.items()})
    data_provider.mark_for_cleanup(source_model)
    source_add_and_check(source_add_args)

    # Create and run a scan
    data_provider.mark_for_cleanup(Scan(name=scan_name))
    scan_add_and_check({"name": scan_name, "sources": source_model.name})

    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"
    assert result["report_id"]

    # Download and verify a report
    is_network_scan = source_definition.type == "network"
    downloaded_report = tmp_path / "report.tar.gz"

    report_download({"scan-job": scan_job_id, "output-file": downloaded_report.as_posix()})

    tarfile.open(downloaded_report).extractall(tmp_path, filter="tar")
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan)
