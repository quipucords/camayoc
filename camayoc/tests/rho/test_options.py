"""Tests for options validation.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""
import io

import pexpect

import pytest


RHO_COMMANDS = (
    "rho",
    "rho auth add",
    "rho auth clear",
    "rho auth edit",
    "rho auth list",
    "rho auth show",
    "rho fact list",
    "rho fact hash",
    "rho profile add",
    "rho profile clear",
    "rho profile edit",
    "rho profile list",
    "rho profile show",
    "rho scan",
)


@pytest.mark.parametrize("command", RHO_COMMANDS)
def test_help_option(isolated_filesystem, command):
    """Test the various commands for the presence of help option.

    :id: db7a08d1-a133-4acf-b1ff-ace38eb31825
    :description: Run the commands passing the ``--help`` option and check if
        it shows the help message.
    :steps: Run ``<command> --help``.
    :expectedresults: The help message is shown and a zero exit code is
        returned.
    """
    process = pexpect.spawn(command + " --help")
    process.logfile = io.BytesIO()
    assert process.expect(pexpect.EOF) == 0
    output = process.logfile.getvalue().decode("utf-8")
    assert len(output) > 0
    assert "Usage: {}".format(command) in output
    if command == "rho":
        assert "Supported modules:" in output
    else:
        assert "Options:" in output
    process.logfile.close()
    process.close()
    assert process.exitstatus == 0


@pytest.mark.parametrize(
    "command", [command for command in RHO_COMMANDS if not command.endswith("list")]
)
def test_help_no_option(isolated_filesystem, command):
    """Test the various commands for the presence of help option.

    :id: 1e55af61-56b8-48c0-9a37-a9dbca11e78d
    :description: Run the commands without passing any option and check if it
        shows the help message.
    :steps: Run ``<command>``.
    :expectedresults: The help message is shown and a non-zero exit code is
        returned.
    """
    process = pexpect.spawn(command)
    process.logfile = io.BytesIO()
    assert process.expect(pexpect.EOF) == 0
    output = process.logfile.getvalue().decode("utf-8")
    assert len(output) > 0
    assert "Usage: {}".format(command) in output
    if command == "rho":
        assert "Supported modules:" in output
    else:
        assert "Options:" in output
    process.logfile.close()
    process.close()
    assert process.exitstatus == 1
