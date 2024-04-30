# coding=utf-8
"""Utility functions for Quipucords cli tests."""

import functools
import itertools
import json
import re
import tarfile
import tempfile
import time
from pprint import pformat

import pexpect

from camayoc.config import settings
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.exceptions import FailedMergeReportException
from camayoc.exceptions import FailedScanException
from camayoc.exceptions import WaitTimeError
from camayoc.utils import client_cmd


def clear_all_entities():
    """Clear all entities from the server.

    We must delete all entities on the server in the correct order, first
    scans, then sources, then credentials.
    """
    error_finder = re.compile("internal server error")
    errors = []
    output = []
    for command in ("scan", "source", "cred"):
        clear_output = pexpect.run("{} {} clear --all".format(client_cmd, command), encoding="utf8")
        errors.extend(error_finder.findall(clear_output))
        output.append(clear_output)
    assert errors == [], output


def config_credentials():
    """Return all credentials available on configuration file for CLI scans."""
    try:
        config_credentials = settings.credentials
    except ConfigFileNotFoundError:
        config_credentials = []

    if not config_credentials:
        return []

    scan_credentials = list(itertools.chain(*[source.credentials for source in config_sources()]))
    return [credential for credential in config_credentials if credential.name in scan_credentials]


def config_sources():
    """Return all sources available on configuration file for CLI scans."""
    try:
        config_sources = settings.sources
    except ConfigFileNotFoundError:
        config_sources = []

    if not config_sources:
        return []

    scan_sources = list(itertools.chain(*[scan.sources for scan in config_scans()]))
    return [source for source in config_sources if source.name in scan_sources]


def config_scans():
    """Return all CLI scans available on the configuration file."""
    try:
        return settings.scans
    except ConfigFileNotFoundError:
        return []


def wait_for_scan(scan_job_id, status="completed", timeout=900):
    """Wait for a scan to reach some ``status`` up to ``timeout`` seconds.

    :param scan_job_id: Scan ID to wait for.
    :param status: Scan status which will wait for. Default is completed.
    :param timeout: wait up to this amount of seconds. Default is 900.
    """
    while timeout > 0:
        result = scan_job({"id": scan_job_id})
        if status != "failed" and result["status"] == "failed":
            raise FailedScanException(
                'The scan with ID "{}" has failed unexpectedly.\n\n'
                "The information about the scan is:\n{}\n".format(scan_job_id, pformat(result))
            )
        if result["status"] == status:
            return
        time.sleep(5)
        timeout -= 5
    raise WaitTimeError(
        'Timeout waiting for scan with ID "{}" to achieve the "{}" status.\n\n'
        "The information about the scan is:\n{}\n".format(scan_job_id, status, pformat(result))
    )


def wait_for_report_merge(job_id, status="completed", timeout=900):
    """Wait for a report merge to reach some ``status`` up to ``timeout`` seconds.

    :param job_id: Merge job ID to wait for.
    :param status: Merge status which will wait for. Default is completed.
    :param timeout: wait up to this amount of seconds. Default is 900.
    """
    while timeout > 0:
        result = job_status({"id": job_id})
        if status != "failed" and result["status"] == "failed":
            raise FailedMergeReportException(
                'The merge report job with ID "{}" has failed '
                "unexpectedly.\n\n"
                "The information about the merge report job is:\n{}\n".format(
                    job_id, pformat(result)
                )
            )
        if result["status"] == status:
            return
        time.sleep(5)
        timeout -= 5
    raise WaitTimeError(
        'Timeout waiting for the merge report job with ID "{}" to achieve '
        'the "{}" status.\n\n'
        "The current information about the merge report job is:\n{}\n".format(
            job_id, status, pformat(result)
        )
    )


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
            command += " --{}".format(key)
        else:
            command += " --{} {}".format(key, value)
    output, command_exitstatus = pexpect.run(
        command, encoding="utf-8", timeout=60, withexitstatus=True
    )
    assert command_exitstatus == exitstatus, output
    return output


def cred_add_and_check(options, inputs=None, exitstatus=0):
    """Add a new credential entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A list of tuples mapping the input prompts and the value to
        be filled. For example::

            inputs=[('prompt1:', 'input1'), ('prompt2:', 'input2')]
    :param exitstatus: Expected exit status code.
    """
    if "type" not in options:
        options["type"] = "network"
    command = "{} -v cred add".format(client_cmd)
    for key, value in options.items():
        if value is None:
            command += " --{}".format(key)
        else:
            command += " --{}={}".format(key, value)
    qpc_cred_add = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_cred_add.expect(prompt) == 0
        qpc_cred_add.sendline(value)
    if "name" in options:
        assert qpc_cred_add.expect('Credential "{}" was added'.format(options["name"])) == 0
    assert qpc_cred_add.expect(pexpect.EOF) == 0
    qpc_cred_add.close()
    assert qpc_cred_add.exitstatus == exitstatus


def cred_show_and_check(options, output, exitstatus=0):
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
    command = "{} -v cred show".format(client_cmd)
    for key, value in options.items():
        if value is None:
            command += " --{}".format(key)
        else:
            command += " --{}={}".format(key, value)
    qpc_cred_show = pexpect.spawn(command)
    assert qpc_cred_show.expect(output) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()
    assert qpc_cred_show.exitstatus == exitstatus


report_detail = functools.partial(cli_command, "{} -v report details".format(client_cmd))
"""Run ``qpc report detail`` with ``options`` and return output."""

report_merge = functools.partial(cli_command, "{} -v report merge".format(client_cmd))
"""Run ``qpc report merge`` with ``options`` and return output."""


def job_status(options=None, exitstatus=0):
    """Run ``qpc scan job`` with ``options`` and return output."""
    output = cli_command("{} -v scan job".format(client_cmd), options, exitstatus)
    return json.loads(output)


report_deployments = functools.partial(cli_command, "{} -v report deployments".format(client_cmd))
"""Run ``qpc report deployments`` with ``options`` and return output."""

report_download = functools.partial(cli_command, "{} -v report download".format(client_cmd))
"""Run ``qpc report download`` with ``options`` and return output."""

report_insights = functools.partial(cli_command, "{} -v report insights".format(client_cmd))
"""Run ``qpc report insights`` with ``options`` and return output."""


def convert_ip_format(ipaddr):
    """Convert IP strings (for generating expected test results)."""
    if ipaddr.endswith("0/24"):
        ipaddr = ipaddr.replace("0/24", r"\[0:255\]")
    elif ipaddr.endswith("0/28"):
        ipaddr = ipaddr.replace("0/28", r"\[0:15\]")
    elif ipaddr.endswith("[1:100]"):
        ipaddr = ipaddr.replace("[1:100]", r"\[1:100\]")
    elif " " in ipaddr:
        ipaddr = '",\r\n        "'.join(ipaddr.split(" "))
    return ipaddr


def source_add_and_check(options, inputs=None, exitstatus=0):
    """Add a new source entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A list of tuples mapping the input prompts and the value to
        be filled. For example::

            inputs=[('prompt1:', 'input1'), ('prompt2:', 'input2')]
    :param exitstatus: Expected exit status code.
    """
    if "cred" in options:
        options["cred"] = " ".join(options["cred"])
    if "hosts" in options:
        options["hosts"] = " ".join(options["hosts"])
    if "exclude-hosts" in options:
        options["exclude-hosts"] = " ".join(options["exclude-hosts"])
    if "type" not in options:
        options["type"] = "network"
    command = "{} -v source add".format(client_cmd)
    for key, value in options.items():
        if value is None:
            command += " --{}".format(key)
        else:
            command += " --{} {}".format(key, value)
    qpc_source_add = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_source_add.expect(prompt) == 0
        qpc_source_add.sendline(value)
    assert qpc_source_add.expect('Source "{}" was added'.format(options["name"])) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == exitstatus


def source_edit_and_check(options, inputs=None, exitstatus=0):
    """Edit an existing source entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param inputs: A list of tuples mapping the input prompts and the value to
        be filled. For example::

            inputs=[('prompt1:', 'input1'), ('prompt2:', 'input2')]
    :param exitstatus: Expected exit status code.
    """
    if "cred" in options:
        options["cred"] = " ".join(options["cred"])
    if "hosts" in options:
        options["hosts"] = " ".join(options["hosts"])
    if "exclude-hosts" in options:
        options["exclude-hosts"] = " ".join(options["exclude-hosts"])
    command = "{} -v source edit".format(client_cmd)
    for key, value in options.items():
        if value is None:
            command += " --{}".format(key)
        else:
            command += " --{} {}".format(key, value)
    qpc_source_edit = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_source_edit.expect(prompt) == 0
        qpc_source_edit.sendline(value)
    assert qpc_source_edit.expect('Source "{}" was updated'.format(options["name"])) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == exitstatus


def source_show_and_check(options, output, exitstatus=0):
    """Show a source entry.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param output: A regular expression pattern that matches the expected
        output. Make sure to escape any regular expression especial character.
    :param exitstatus: Expected exit status code.
    """
    command = "{} -v source show".format(client_cmd)
    for key, value in options.items():
        if value is None:
            command += " --{}".format(key)
        else:
            command += " --{}={}".format(key, value)
    qpc_source_show = pexpect.spawn(command)
    assert qpc_source_show.expect(output) == 0
    assert qpc_source_show.expect(pexpect.EOF) == 0
    qpc_source_show.close()
    assert qpc_source_show.exitstatus == exitstatus


def scan_add_and_check(options, status_message_regex=None, exitstatus=0):
    """Run ``qpc scan add`` command with ``options`` returning its output.

    :param options: A dictionary mapping the option names and their values.
    :param status_message_regex: Regex to match against output message.
    :param exitstatus: Expected exit status for running command.
    """
    assert options is not {}
    assert options.get("name") is not None
    if not status_message_regex:
        status_message_regex = r'Scan "{}" was added.'.format(options["name"])
    result = scan_add(options, exitstatus)
    match = re.search(status_message_regex, result)
    assert match is not None


def scan_edit_and_check(options, status_message_regex, exitstatus=0):
    """Run ``qpc scan edit`` command with ``options`` returning its output.

    :param options: A dictionary mapping the option names and their values.
    :param status_message_regex: Regex to match against output message.
    :param exitstatus: Expected exit status for runnign command.
    """
    assert options is not {}
    assert options.get("name") is not None

    result = scan_edit(options, exitstatus)
    match = re.match(status_message_regex, result)
    assert match is not None


def scan_show_and_check(scan_name, expected_result=None):
    """Run ``qpc scan show`` command with ``options`` returning its output.

    :param options: A dictionary mapping the option names and their values.
        Pass ``None`` for flag options.
    :param output: A regular expression pattern that matches the expected
        output. Make sure to escape any regular expression especial character.
    :param exitstatus: Expected exit status code.
    """
    scan_show_result = scan_show({"name": scan_name})
    scan_show_result = json.loads(scan_show_result)
    if expected_result is not None:
        expected_result["id"] = scan_show_result["id"]
        assert expected_result == scan_show_result


scan_cancel = functools.partial(cli_command, "{} -v scan cancel".format(client_cmd))
"""Run ``qpc scan cancel`` command with ``options`` returning its output."""

scan_add = functools.partial(cli_command, "{} -v scan add".format(client_cmd))
"""Run ``qpc scan add`` command with ``options`` returning its output."""

scan_clear = functools.partial(cli_command, "{} -v scan clear".format(client_cmd))
"""Run ``qpc scan clear`` returning its output."""

scan_edit = functools.partial(cli_command, "{} -v scan edit".format(client_cmd))
"""Run ``qpc scan edit`` command with ``options`` returning its output."""

scan_show = functools.partial(cli_command, "{} -v scan show".format(client_cmd))
"""Run ``qpc scan show`` command with ``options`` returning its output."""

scan_start = functools.partial(cli_command, "{} -v scan start".format(client_cmd))
"""Run ``qpc scan start`` command with ``options`` returning its output."""

source_show = functools.partial(cli_command, "{} source show".format(client_cmd))
"""Run ``qpc source show`` command with ``options`` returning its output."""


def scan_job(options=None, exitstatus=0):
    """Run ``qpc scan job`` command with ``options`` returning its output."""
    return json.loads(cli_command("{} -v scan job".format(client_cmd), options, exitstatus))


def retrieve_report(scan_job_id):
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_file = f"{tmpdirname}/report.tar.gz"
        report_download({"scan-job": scan_job_id, "output-file": output_file})
        details = deployments = None
        with tarfile.open(output_file) as pkg:
            for member in pkg.getmembers():
                if member.name.endswith("details.json"):
                    data = pkg.extractfile(member).read()
                    details = json.loads(data)
                if member.name.endswith("deployments.json"):
                    data = pkg.extractfile(member).read()
                    deployments = json.loads(data)
    return details, deployments


def setup_qpc():
    """Configure and login qpc with Camayoc's configuration info.

    The minimum required configuration is both ``hostname`` and ``port``, for
    example::

        qpc:
          hostname: localhost
          port: 8000

    If not specified ``https``, ``ssl-verify``, ``username`` and ``password``
    will use their default values: ``false``, ``false``, ``admin`` and ``pass``
    respectively.

    See below an example with all fields being defined::

        qpc:
          hostname: quipucords.example.com
          https: true
          password: youshallnotpass
          port: 443
          ssl-verify: /path/to/custom/certificate
          username: gandalf
    """
    qpc_config = settings.quipucords_server

    https = ""
    if not qpc_config.https:
        https = " --use-http"

    ssl_verify = ""
    if not isinstance(qpc_config.ssl_verify, bool):
        ssl_verify = " --ssl-verify={}".format(qpc_config.ssl_verify)

    command = "{} server config --host {} --port {}{}{}".format(
        client_cmd, qpc_config.hostname, qpc_config.port, https, ssl_verify
    )
    output, exitstatus = pexpect.run(command, encoding="utf8", withexitstatus=True)
    assert exitstatus == 0, output

    # now login to the server
    command = "{} server login --username {}".format(client_cmd, qpc_config.username)
    output, exitstatus = pexpect.run(
        command,
        encoding="utf8",
        events=[("Password: ", qpc_config.password + "\n")],
        withexitstatus=True,
    )
    assert exitstatus == 0, output
