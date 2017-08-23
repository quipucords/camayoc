# coding=utf-8
"""Values usable by multiple test modules."""
from camayoc import utils


MASKED_PASSWORD_OUTPUT = '\*{8}'
"""Regex that matches password on outputs."""

CONNECTION_PASSWORD_INPUT = 'Provide connection password.\r\nPassword:'
"""Connection password input prompt."""

SUDO_PASSWORD_INPUT = 'Provide password for sudo.\r\nPassword:'
"""Sudo password input prompt."""

VAULT_PASSWORD = utils.uuid4()
"""Vault password will be unique across Python sessions."""

VAULT_PASSWORD_INPUT = 'Please enter your rho vault password:'
"""Vault password input prompt."""
