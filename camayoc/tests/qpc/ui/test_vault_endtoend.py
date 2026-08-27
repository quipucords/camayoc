# coding=utf-8
"""End-to-end UI tests for vault-backed Ansible credentials.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

import tarfile

import pytest

from camayoc.config import settings
from camayoc.qpc_models import Scan
from camayoc.tests.qpc.cli.utils import clear_server_vault
from camayoc.tests.qpc.cli.utils import configure_server_vault
from camayoc.tests.qpc.utils import assert_ansible_logs
from camayoc.tests.qpc.utils import assert_sha256sums
from camayoc.types.settings import VaultAnsibleCredentialOptions
from camayoc.ui import Client
from camayoc.ui import data_factories
from camayoc.ui.data_factories import AnsibleSourceFormDTOFactory
from camayoc.ui.data_factories import TriggerScanDTOFactory
from camayoc.ui.data_factories import VaultAnsibleCredentialFormDTOFactory
from camayoc.ui.enums import CredentialTypes
from camayoc.ui.enums import MainMenuPages


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


@pytest.mark.slow
@pytest.mark.runs_scan
@pytest.mark.skipif(
    not _VAULT_ANSIBLE_SOURCES,
    reason="No vault-backed ansible sources configured",
)
@pytest.mark.parametrize("source_definition", _VAULT_ANSIBLE_SOURCES)
def test_vault_ansible_endtoend(
    tmp_path, configured_vault_server, cleaning_data_provider, ui_client: Client, source_definition
):
    """End-to-end test for vault-backed Ansible credential via UI.

    :id: c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f
    :description: Complete user journey through UI using vault-backed Ansible
        credential - create credential, create source, run scan, download report.
    :steps:
        1) Configure global HashiCorp Vault settings on the server
        2) Log into the UI
        3) Go to Credentials page and create a vault-backed Ansible credential
        4) Go to Sources page and create an Ansible source using the vault credential
        5) Trigger a scan for the newly created source
        6) Wait for scan to complete
        7) Download scan report
        8) Log out
        9) Validate the downloaded report contains ansible data
    :expectedresults: Vault configuration succeeds, credential and source are
        created via UI, scan completes successfully, and the report contains
        valid ansible instance_details and hosts facts.
    """
    # Get vault credential configuration from settings
    credentials_by_name = {credential.name: credential for credential in settings.credentials}
    vault_credential_config = credentials_by_name[source_definition.credentials[0]]

    # Create vault credential DTO with real vault paths from configuration
    credential_form = VaultAnsibleCredentialFormDTOFactory(
        vault_secret_path=vault_credential_config.vault_secret_path,
        vault_secret_key=vault_credential_config.vault_secret_key,
        vault_mount_point=vault_credential_config.vault_mount_point,
    )
    credential_dto = data_factories.AddCredentialDTOFactory(
        credential_type=CredentialTypes.ANSIBLE,
        credential_form=credential_form,
    )

    # Create Ansible source DTO
    source_form = AnsibleSourceFormDTOFactory(
        address=source_definition.hosts[0],
        credentials=[credential_form.credential_name],
    )
    if hasattr(source_definition, "port") and source_definition.port:
        source_form.port = str(source_definition.port)
    if hasattr(source_definition.options, "ssl_cert_verify"):
        source_form.verify_ssl = source_definition.options.ssl_cert_verify

    source_dto = data_factories.AddSourceDTOFactory(
        source_type=data_factories.SourceTypes.ANSIBLE_CONTROLLER,
        source_form=source_form,
    )

    # Create scan DTO
    trigger_scan_dto = TriggerScanDTOFactory(
        source_name=source_form.source_name,
        scan_form__jboss_eap=None,
        scan_form__fuse=None,
        scan_form__jboss_web_server=None,
    )

    # Mark for cleanup
    cleaning_data_provider.mark_for_cleanup(
        credential_form.to_model(),
        source_form.to_model(),
        Scan(name=trigger_scan_dto.scan_form.scan_name),
    )

    # Execute UI workflow
    (
        ui_client.begin()
        .login(data_factories.LoginFormDTOFactory())
        .navigate_to(MainMenuPages.CREDENTIALS)
        .add_credential(credential_dto)
        .navigate_to(MainMenuPages.SOURCES)
        .add_source(source_dto)
        .trigger_scan(trigger_scan_dto)
        .navigate_to(MainMenuPages.SCANS)
        .download_scan(trigger_scan_dto.scan_form.scan_name)
        .logout()
    )

    # Validate downloaded report
    downloaded_report = ui_client.downloaded_files[-1]

    with tarfile.open(downloaded_report.path()) as archive:
        archive.extractall(tmp_path, filter="data")

    # Verify report integrity and ansible-specific content
    assert_sha256sums(tmp_path)
    assert_ansible_logs(tmp_path, is_network_scan=False)
