from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from camayoc.config import get_settings

EXAMPLE_CONFIG_PATH = Path(__file__).parent / "../example_config.yaml"
with open(EXAMPLE_CONFIG_PATH) as fh:
    EXAMPLE_CONFIG = yaml.load(fh, Loader=yaml.FullLoader)

# FIXME: this should be an enum
SOURCE_TYPES = ("network", "satellite", "vcenter")

VAULT_SERVER_CONFIG = {
    "address": "vault.example.com",
    "port": 8200,
    "client_cert": "/path/to/client.crt",
    "client_key": "/path/to/client.key",
    "ca_cert": "/path/to/ca.crt",
}

VAULT_OPENSHIFT_CRED = {
    "name": "OpenShiftVault",
    "type": "openshift",
    "vault_secret_path": "vault/dev/ocp-token",
    "vault_secret_key": "auth_token",
    "vault_mount_point": "discovery",
}

VAULT_OPENSHIFT_SOURCE = {
    "hosts": ["api.vault-ocp.example.com"],
    "credentials": ["OpenShiftVault"],
    "name": "OpenShiftVault",
    "type": "openshift",
    "ssl_cert_verify": False,
}

VAULT_ANSIBLE_CRED = {
    "name": "AnsibleVault",
    "type": "ansible",
    "vault_secret_path": "vault/dev/aap-token",
    "vault_secret_key": "password",
}

VAULT_ANSIBLE_SOURCE = {
    "hosts": ["aap.example.com"],
    "credentials": ["AnsibleVault"],
    "name": "AnsibleVault",
    "type": "ansible",
    "ssl_cert_verify": False,
}


@pytest.fixture
def example_config():
    return deepcopy(EXAMPLE_CONFIG)


def write_config(tmp_path, config):
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as fh:
        yaml.dump(data=config, stream=fh)
    return config_file


def test_read_example_config():
    settings = get_settings(path=EXAMPLE_CONFIG_PATH)
    assert settings.quipucords_server
    assert settings.hashicorp_vault is None
    vault_creds = [c for c in settings.credentials if hasattr(c, "vault_secret_path")]
    assert vault_creds == []


def test_valid_hashicorp_vault_config(tmp_path, example_config):
    example_config["hashicorp_vault"] = VAULT_SERVER_CONFIG
    config_file = write_config(tmp_path, example_config)

    settings = get_settings(config_file)

    assert settings.hashicorp_vault is not None
    assert settings.hashicorp_vault.address == "vault.example.com"
    assert settings.hashicorp_vault.port == 8200
    assert settings.hashicorp_vault.client_cert == Path("/path/to/client.crt")
    assert settings.hashicorp_vault.client_key == Path("/path/to/client.key")
    assert settings.hashicorp_vault.ca_cert == Path("/path/to/ca.crt")


def test_hashicorp_vault_requires_ca_cert(tmp_path, example_config):
    vault_config = {**VAULT_SERVER_CONFIG}
    vault_config.pop("ca_cert")
    example_config["hashicorp_vault"] = vault_config
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_valid_vault_openshift_credential(tmp_path, example_config):
    example_config["hashicorp_vault"] = VAULT_SERVER_CONFIG
    example_config["credentials"].append(VAULT_OPENSHIFT_CRED)
    example_config["sources"].append(VAULT_OPENSHIFT_SOURCE)
    config_file = write_config(tmp_path, example_config)

    settings = get_settings(config_file)

    credential = next(c for c in settings.credentials if c.name == "OpenShiftVault")
    assert credential.vault_secret_path == "vault/dev/ocp-token"
    assert credential.vault_secret_key == "auth_token"
    assert credential.vault_mount_point == "discovery"


def test_valid_vault_ansible_credential(tmp_path, example_config):
    example_config["hashicorp_vault"] = VAULT_SERVER_CONFIG
    example_config["credentials"].append(VAULT_ANSIBLE_CRED)
    example_config["sources"].append(VAULT_ANSIBLE_SOURCE)
    config_file = write_config(tmp_path, example_config)

    settings = get_settings(config_file)

    credential = next(c for c in settings.credentials if c.name == "AnsibleVault")
    assert credential.vault_secret_path == "vault/dev/aap-token"
    assert credential.vault_secret_key == "password"
    assert credential.vault_mount_point is None


def test_invalid_vault_credential_without_vault_config(tmp_path, example_config):
    example_config["credentials"].append(VAULT_OPENSHIFT_CRED)
    example_config["sources"].append(VAULT_OPENSHIFT_SOURCE)
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


@pytest.mark.parametrize("missing_field", ("vault_secret_path", "vault_secret_key"))
def test_invalid_vault_credential_missing_required_field(tmp_path, example_config, missing_field):
    example_config["hashicorp_vault"] = VAULT_SERVER_CONFIG
    credential = {
        "name": "OpenShiftVaultMissing",
        "type": "openshift",
        "vault_secret_path": "vault/dev/ocp-token",
        "vault_secret_key": "auth_token",
    }
    credential.pop(missing_field)
    example_config["credentials"].append(credential)
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_vault_credential_source_type_mismatch(tmp_path, example_config):
    example_config["hashicorp_vault"] = VAULT_SERVER_CONFIG
    example_config["credentials"].append(
        {
            "name": "OpenShiftVaultMismatch",
            "type": "openshift",
            "vault_secret_path": "vault/dev/ocp-token",
            "vault_secret_key": "auth_token",
        }
    )
    example_config["sources"].append(
        {
            "hosts": ["api.vault-ocp.example.com"],
            "credentials": ["OpenShiftVaultMismatch"],
            "name": "OpenShiftVaultMismatch",
            "type": "network",
            "ssl_cert_verify": False,
        }
    )
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_missing_section(tmp_path, example_config):
    example_config.pop("quipucords_server")
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


@pytest.mark.parametrize("option", ("credentials", "sources", "scans"))
def test_invalid_not_unique_names(tmp_path, example_config, option):
    example_config[option].append(example_config[option][0])
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_non_existing_credential(tmp_path, faker, example_config):
    new_source = {
        "hosts": [faker.ipv4()],
        "name": faker.name(),
        "type": "network",
        "credentials": [faker.name()],
    }
    example_config["sources"].append(new_source)
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_non_existing_source(tmp_path, faker, example_config):
    new_scan = {"name": faker.name(), "sources": [faker.name()]}
    example_config["scans"].append(new_scan)
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)


@pytest.mark.parametrize("stype", SOURCE_TYPES)
def test_invalid_source_credential_type_mismatch(tmp_path, faker, example_config, stype):
    new_type = faker.random_element([_ for _ in SOURCE_TYPES if _ != stype])
    source = faker.random_element(
        [source for source in example_config.get("sources") if source.get("type") == stype]
    )
    credential_name = faker.random_element(source.get("credentials"))
    credential = faker.random_element(
        [
            credential
            for credential in example_config.get("credentials")
            if credential.get("name") == credential_name
        ]
    )
    credential["type"] = new_type
    if new_type in ("satellite", "vcenter", "openshift") and not credential.get("password"):
        credential["password"] = faker.password()
    config_file = write_config(tmp_path, example_config)

    with pytest.raises(ValidationError):
        get_settings(config_file)
