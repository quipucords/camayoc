# coding=utf-8
"""Utility functions for Quipucords cli tests."""
import functools
import io
import json

import pexpect


def cli_command(command, options=None, exitstatus=0):
    """Run a cli ``command`` with the ``options``.

    :param command: the base command to be run
    :param options: dictionary mapping the command options. Each item will be
        mapped to ``--key value``, if the item's value is ``None`` then a flag
        option will be created ``--key``.
    :param exitstatus: expected exit status. If for some reason the command
        exit status is different then an AssertionError will be raised with the
        command output as the exception messege.
    """
    if options is None:
        options = {}
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{} {}'.format(key, value)
    child = pexpect.spawn(command)
    child.logfile = io.BytesIO()
    assert child.expect(pexpect.EOF) == 0
    child.close()
    output = child.logfile.getvalue().decode('utf-8')
    assert child.exitstatus == exitstatus, output
    return output


def cred_add(options, inputs=None, exitstatus=0):
    """Add a new credential entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A list of tuples mapping the input prompts and the value to
        be filled. For example::

            inputs=[('prompt1:', 'input1'), ('prompt2:', 'input2')]
    :param exitstatus: Expected exit status code.
    """
    if 'type' not in options:
        options['type'] = 'network'
    options.pop('rho', None)  # need to remove this data that is rho specific
    command = 'qpc cred add'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    qpc_cred_add = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_cred_add.expect(prompt) == 0
        qpc_cred_add.sendline(value)
    if 'name' in options:
        assert qpc_cred_add.expect(
            'Credential "{}" was added'.format(options['name'])) == 0
    assert qpc_cred_add.expect(pexpect.EOF) == 0
    qpc_cred_add.close()
    assert qpc_cred_add.exitstatus == exitstatus


def cred_show(options, output, exitstatus=0):
    r"""Show a credential entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param output: An OrderedDict mapping the output fields and their values.
        The order the fields were inserted in the OrderedDict will be the same
        order they will be present on the output. If cred_type and/or id fields
        are not present on the output they will be added with the value of
        network and \d+ respectively.
    :param exitstatus: Expected exit status code.
    """
    command = 'qpc cred show'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    qpc_cred_show = pexpect.spawn(command)
    assert qpc_cred_show.expect(output) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()
    assert qpc_cred_show.exitstatus == exitstatus


report_detail = functools.partial(cli_command, 'qpc report detail')
"""Run ``qpc report detail`` with ``options`` and return output."""


def source_add(options, inputs=None, exitstatus=0):
    """Add a new source entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A list of tuples mapping the input prompts and the value to
        be filled. For example::

            inputs=[('prompt1:', 'input1'), ('prompt2:', 'input2')]
    :param exitstatus: Expected exit status code.
    """
    if 'cred' in options:
        options['cred'] = ' '.join(options['cred'])
    if 'hosts' in options:
        options['hosts'] = ' '.join(options['hosts'])
    if 'type' not in options:
        options['type'] = 'network'
    command = 'qpc source add'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    qpc_source_add = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_source_add.expect(prompt) == 0
        qpc_source_add.sendline(value)
    assert qpc_source_add.expect(
        'Source "{}" was added'.format(options['name'])) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == exitstatus


def source_show(options, output, exitstatus=0):
    """Show a source entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param output: A regular expression pattern that matches the expected
        output. Make sure to escape any regular expression especial character.
    :param exitstatus: Expected exit status code.
    """
    command = 'qpc source show'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    qpc_source_show = pexpect.spawn(command)
    assert qpc_source_show.expect(output) == 0
    assert qpc_source_show.expect(pexpect.EOF) == 0
    qpc_source_show.close()
    assert qpc_source_show.exitstatus == exitstatus


scan_cancel = functools.partial(cli_command, 'qpc scan cancel')
"""Run ``qpc scan cancel`` command with ``options`` returning its output."""

scan_pause = functools.partial(cli_command, 'qpc scan pause')
"""Run ``qpc scan pause`` command with ``options`` returning its output."""

scan_restart = functools.partial(cli_command, 'qpc scan restart')
"""Run ``qpc scan restart`` command with ``options`` returning its output."""

scan_add = functools.partial(cli_command, 'qpc scan add')
"""Run ``qpc scan add`` command with ``options`` returning its output."""

scan_start = functools.partial(cli_command, 'qpc scan start')
"""Run ``qpc scan start`` command with ``options`` returning its output."""


def scan_job(options=None, exitstatus=0):
    """Run ``qpc scan job`` command with ``options`` returning its output."""
    return json.loads(cli_command('qpc scan job', options, exitstatus))
