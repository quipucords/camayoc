from unittest import mock

from camayoc.qpc_models import Credential


def test_vault_credential_sets_vault_fields():
    """A vault-backed Credential exposes its vault fields in the payload."""
    with mock.patch("camayoc.api.Client"):
        cred = Credential(
            cred_type="ansible",
            name="vault-cred",
            vault_secret_path="/secret/data/ansible",
            vault_secret_key="password",
            vault_mount_point="secret",
        )

    assert cred.vault_secret_path == "/secret/data/ansible"
    assert cred.vault_secret_key == "password"
    assert cred.vault_mount_point == "secret"

    payload = cred.payload()
    assert payload["vault_secret_path"] == "/secret/data/ansible"
    assert payload["vault_secret_key"] == "password"
    assert payload["vault_mount_point"] == "secret"
    # Vault credentials authenticate via the secret path, so no username is
    # auto-generated and non-vault auth fields stay empty.
    assert payload["username"] is None
    assert payload["password"] is None
    assert payload["auth_token"] is None


def test_vault_credential_omits_unset_mount_point():
    """An unset vault_mount_point is not added to the payload."""
    with mock.patch("camayoc.api.Client"):
        cred = Credential(
            cred_type="openshift",
            name="vault-cred-no-mount",
            vault_secret_path="/secret/data/openshift",
            vault_secret_key="token",
        )

    assert cred.vault_secret_path == "/secret/data/openshift"
    assert cred.vault_secret_key == "token"
    assert not hasattr(cred, "vault_mount_point")
    assert "vault_mount_point" not in cred.payload()


def test_non_vault_credential_has_no_vault_fields():
    """A regular Credential does not gain vault attributes or payload keys."""
    with mock.patch("camayoc.api.Client"):
        cred = Credential(
            cred_type="network",
            name="plain-cred",
            username="user",
            password="pass",
        )

    assert not hasattr(cred, "vault_secret_path")
    assert not hasattr(cred, "vault_secret_key")
    assert not hasattr(cred, "vault_mount_point")
    payload = cred.payload()
    assert "vault_secret_path" not in payload
    assert "vault_secret_key" not in payload
    assert "vault_mount_point" not in payload
