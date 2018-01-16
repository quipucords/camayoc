# coding=utf-8
"""Utility functions for Quipucords cli tests."""
import pexpect


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
    expected_output = '{\r\n'
    if 'cred_type' not in output:
        expected_output += '    "cred_type": "network",\r\n'
    if 'id' not in output:
        expected_output += '    "id": \\d+,\r\n'
    expected_output += ',\r\n'.join([
        '    "{}": "{}"'.format(key, value)
        for key, value in output.items()
    ])
    expected_output += '\r\n}\r\n'

    command = 'qpc cred show'
    for key, value in options.items():
        if value is None:
            command += ' --{}'.format(key)
        else:
            command += ' --{}={}'.format(key, value)
    qpc_cred_show = pexpect.spawn(command)
    assert qpc_cred_show.expect(expected_output) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()
    assert qpc_cred_show.exitstatus == exitstatus


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
    qpc_cred_show = pexpect.spawn(command)
    assert qpc_cred_show.expect(output) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()
    assert qpc_cred_show.exitstatus == exitstatus
