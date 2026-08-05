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
from camayoc.tests.qpc.cli.utils import configure_server_vault
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import retrieve_report
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import source_add_and_check
from camayoc.tests.qpc.cli.utils import wait_for_scan
from camayoc.types.settings import SourceOptions
from camayoc.types.settings import VaultAnsibleCredentialOptions


def _vault_ansible_credentials_for_source(source_definition: SourceOptions):
    credentials_by_name = {credential.name: credential for credential in settings.credentials}
    for credential_name in source_definition.credentials:
        credential = credentials_by_name.get(credential_name)
        if isinstance(credential, VaultAnsibleCredentialOptions):
            yield credential


def vault_ansible_sources():
    """Yield ansible sources that use vault-backed credentials.

    Skips collection when ``hashicorp_vault`` or matching sources are missing.
    """
    if settings.hashicorp_vault is None:
        return

    for source_definition in settings.sources:
        if source_definition.type != "ansible":
            continue
        if not any(_vault_ansible_credentials_for_source(source_definition)):
            continue
        yield pytest.param(source_definition, id=source_definition.name)


_VAULT_ANSIBLE_SOURCES = list(vault_ansible_sources())
_SKIP_NO_VAULT_ANSIBLE = pytest.mark.skip(
    reason="No hashicorp_vault config or vault-backed ansible sources configured"
)


def _merged_facts(facts):
    """Merge per-system fact dicts from the details report into one mapping."""
    merged = {}
    for fact in facts or []:
        merged.update(fact)
    return merged


def validate_ansible_vault_report(source_name, details, deployments):
    """Validate report attributes expected from a successful vault-backed AAP scan."""
    assert details is not None, "details report missing from download"
    assert deployments is not None, "deployments report missing from download"

    ansible_sources_in_report = [
        report_source
        for report_source in details.get("sources", [])
        if report_source.get("source_type") == "ansible"
    ]
    assert len(ansible_sources_in_report) == 1
    report_source = ansible_sources_in_report[0]
    assert report_source.get("source_name") == source_name

    fact = _merged_facts(report_source.get("facts"))
    assert "instance_details" in fact
    assert "hosts" in fact

    instance_details = fact["instance_details"]
    system_name = instance_details.get("system_name")
    version = instance_details.get("version")
    assert isinstance(system_name, str) and system_name
    assert isinstance(version, str) and version
    assert isinstance(fact["hosts"], list)

    ansible_fingerprints = [
        fingerprint
        for fingerprint in deployments.get("system_fingerprints", [])
        if fingerprint.get("name") == system_name
        and any(source.get("source_type") == "ansible" for source in fingerprint.get("sources", []))
    ]
    assert len(ansible_fingerprints) >= 1
    assert ansible_fingerprints[0].get("os_version") == version


@pytest.fixture
def configured_vault_server(qpc_server_config):
    """Configure Discovery server vault settings from Camayoc config, or skip."""
    if settings.hashicorp_vault is None:
        pytest.skip("hashicorp_vault is not configured in camayoc config")
    configure_server_vault()


@pytest.mark.runs_scan
@pytest.mark.parametrize(
    "source_definition",
    _VAULT_ANSIBLE_SOURCES
    or [pytest.param(None, id="no-vault-ansible-config", marks=_SKIP_NO_VAULT_ANSIBLE)],
)
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
    vault_credential = next(_vault_ansible_credentials_for_source(source_definition))

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

    source_options = {
        "name": source_name,
        "type": "ansible",
        "hosts": source_definition.hosts,
        "cred": [cred_name],
    }
    if source_definition.port is not None:
        source_options["port"] = source_definition.port
    if source_definition.ssl_cert_verify is not None:
        source_options["ssl-cert-verify"] = str(source_definition.ssl_cert_verify).lower()
    if source_definition.disable_ssl is not None:
        source_options["disable-ssl"] = str(source_definition.disable_ssl).lower()
    if source_definition.ssl_protocol is not None:
        source_options["ssl-protocol"] = source_definition.ssl_protocol

    source_add_and_check(source_options)
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

    details, deployments = retrieve_report(scan_job_id)
    validate_ansible_vault_report(source_name, details, deployments)
