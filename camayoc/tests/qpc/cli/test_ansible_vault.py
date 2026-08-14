"""End-to-end CLI tests for Ansible/AAP scans with Vault-backed credentials.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import re
from uuid import uuid4

import pytest

from camayoc.config import settings
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import Source
from camayoc.tests.qpc.cli.test_ansible import validate_ansible_report_minimum
from camayoc.tests.qpc.cli.utils import clear_server_vault
from camayoc.tests.qpc.cli.utils import configure_server_vault
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import retrieve_report
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import source_add_and_check
from camayoc.tests.qpc.cli.utils import source_to_cli_options
from camayoc.tests.qpc.cli.utils import wait_for_scan
from camayoc.types.settings import SourceOptions
from camayoc.types.settings import VaultAnsibleCredentialOptions


def vault_ansible_sources():
    """Yield ansible sources that use a vault-backed credential."""
    credentials_by_name = {credential.name: credential for credential in settings.credentials}
    for source_definition in settings.sources:
        if source_definition.type != "ansible":
            continue
        credential = credentials_by_name.get(source_definition.credentials[0])
        if not isinstance(credential, VaultAnsibleCredentialOptions):
            continue
        yield pytest.param(source_definition, id=source_definition.name)


_VAULT_ANSIBLE_SOURCES = list(vault_ansible_sources())


@pytest.fixture
def configured_vault_server(qpc_server_config):
    """Configure Discovery server vault settings for the test, then clear them."""
    clear_server_vault()
    configure_server_vault()
    yield
    clear_server_vault()


@pytest.mark.runs_scan
@pytest.mark.skipif(
    not _VAULT_ANSIBLE_SOURCES,
    reason="No vault-backed ansible sources configured",
)
@pytest.mark.parametrize("source_definition", _VAULT_ANSIBLE_SOURCES)
def test_ansible_scan_with_vault_credential(
    configured_vault_server, data_provider, source_definition: SourceOptions
):
    """Scan an AAP source using a vault-backed Ansible credential via CLI.

    :id: 7c2e9a14-5b8d-4f31-9c6a-2e4d8f0b1a55
    :description: Create a vault-backed Ansible credential and ansible source
        through the CLI, run a scan, and validate the downloaded report. This
        covers the HashiCorp Vault credential flow from server vault
        configuration through scan execution and report generation.
    :steps:
        1. Configure global HashiCorp Vault settings on the server via CLI
        2. Create an Ansible credential that references a Vault secret
        3. Create an ansible source that uses that credential
        4. Perform a scan and wait for completion
        5. Download and validate the report
    :expectedresults: Vault configuration succeeds, credential and source are
        created, the scan completes, and the report contains ansible
        instance_details and hosts facts with a matching fingerprint.
    """
    credentials_by_name = {credential.name: credential for credential in settings.credentials}
    vault_credential = credentials_by_name[source_definition.credentials[0]]

    cred_name = str(uuid4())
    source_name = str(uuid4())
    scan_name = str(uuid4())

    cred_options = {
        "name": cred_name,
        "type": "ansible",
        "vault-secret-path": vault_credential.vault_secret_path,
        "vault-secret-key": vault_credential.vault_secret_key,
    }
    if vault_credential.vault_mount_point is not None:
        cred_options["vault-mount-point"] = vault_credential.vault_mount_point

    cred_add_and_check(cred_options)
    data_provider.mark_for_cleanup(Credential(name=cred_name, cred_type="ansible"))

    source_add_and_check(
        source_to_cli_options(
            source_definition,
            name=source_name,
            credentials=[cred_name],
            source_type="ansible",
        )
    )
    data_provider.mark_for_cleanup(Source(name=source_name, source_type="ansible"))

    scan_add_and_check({"name": scan_name, "sources": source_name})
    data_provider.mark_for_cleanup(Scan(name=scan_name))

    output = scan_start({"name": scan_name})
    match_scan_id = re.match(r'Scan "(\d+)" started.', output)
    assert match_scan_id is not None
    scan_job_id = match_scan_id.group(1)

    wait_for_scan(scan_job_id)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"

    details, deployments, aggregate = retrieve_report(scan_job_id)
    validate_ansible_report_minimum(source_name, details, deployments, aggregate)
