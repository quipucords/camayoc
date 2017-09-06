# coding=utf-8
"""Utility functions for RHO tests."""
import pexpect

from camayoc.constants import (
    VAULT_PASSWORD,
    VAULT_PASSWORD_INPUT,
)


def input_vault_password(process, vault_password=VAULT_PASSWORD):
    """Expect the vault password input and input the vault password.

    :param process: A pexpect object returned by the ``pexpect.spawn``.
    :param vault_password: The vault password to be used, defaults to
        :data:`camayoc.constants.VAULT_PASSWORD`.
    """
    assert process.expect(VAULT_PASSWORD_INPUT) == 0
    process.sendline(vault_password)


def auth_add(
        options, inputs=None, exitstatus=0, vault_password=VAULT_PASSWORD):
    """Add a new auth entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A dictionary mapping the input prompts and the value to be
        filled.
    :param exitstatus: Expected exit status code.
    :param vault_password: The vault password to be used, defaults to
        :data:`camayoc.constants.VAULT_PASSWORD`.
    """
    command = 'rho auth add'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    rho_auth_add = pexpect.spawn(command)
    input_vault_password(rho_auth_add, vault_password)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert rho_auth_add.expect(prompt) == 0
        rho_auth_add.sendline(value)
    if 'name' in options:
        assert rho_auth_add.expect(
            'Auth "{}" was added'.format(options['name'])) == 0
    assert rho_auth_add.expect(pexpect.EOF) == 0
    rho_auth_add.close()
    assert rho_auth_add.exitstatus == exitstatus
