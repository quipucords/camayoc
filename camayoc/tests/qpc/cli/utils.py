# coding=utf-8
"""Utility functions for Quipucords cli tests."""

import functools
import ipaddress
import json
import logging
import re
import tarfile
import tempfile
import time
from pprint import pformat

import pexpect

from camayoc.config import settings
from camayoc.constants import CLI_DEBUG_MSG
from camayoc.exceptions import FailedScanException
from camayoc.exceptions import WaitTimeError
from camayoc.utils import client_cmd

logger = logging.getLogger(__name__)


def clear_all_entities():
    """Clear all entities from the server.

    We must delete all entities on the server in the correct order, first
    scans, then sources, then credentials.
    """
    error_finder = re.compile("internal server error")
    errors = []
    output = []
    for command in ("scan", "source", "cred"):
        full_command = "{} {} clear --all".format(client_cmd, command)
        logger.debug(CLI_DEBUG_MSG, full_command)
        clear_output = pexpect.run(full_command, encoding="utf8")
        errors.extend(error_finder.findall(clear_output))
        output.append(clear_output)
    assert errors == [], output


def wait_for_scan(scan_job_id, status="completed", timeout=settings.camayoc.scan_timeout):
    """Wait for a scan to reach some ``status`` up to ``timeout`` seconds.

    :param scan_job_id: Scan ID to wait for.
    :param status: Scan status which will wait for. Default is completed.
    :param timeout: wait up to this amount of seconds. Default is camayoc.scan_timeout.
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
    logger.debug(CLI_DEBUG_MSG, command)
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
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_cred_add = pexpect.spawn(command)
    if inputs is None:
        inputs = []
    for prompt, value in inputs:
        assert qpc_cred_add.expect(prompt) == 0
        qpc_cred_add.sendline(value)
        # SSH key (and potentially other fields in the future) is multiline input,
        # which requires signaling end of input with ^D. Unfortunately, inputs
        # is a list of 2-tuples and we can't mark *some* inputs as multiline
        # without modifying all calls that have `inputs` param...
        if "private ssh key" in prompt.lower():
            qpc_cred_add.sendcontrol("d")
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
    logger.debug(CLI_DEBUG_MSG, command)
    qpc_cred_show = pexpect.spawn(command)
    assert qpc_cred_show.expect(output) == 0
    assert qpc_cred_show.expect(pexpect.EOF) == 0
    qpc_cred_show.close()
    assert qpc_cred_show.exitstatus == exitstatus


report_detail = functools.partial(cli_command, "{} -v report details".format(client_cmd))
"""Run ``qpc report detail`` with ``options`` and return output."""

report_merge = functools.partial(cli_command, "{} -v report merge".format(client_cmd))
"""Run ``qpc report merge`` with ``options`` and return output."""

report_upload = functools.partial(cli_command, "{} -v report upload".format(client_cmd))
"""Run ``qpc report upload`` with ``options`` and return output."""


report_deployments = functools.partial(cli_command, "{} -v report deployments".format(client_cmd))
"""Run ``qpc report deployments`` with ``options`` and return output."""

report_download = functools.partial(cli_command, "{} -v report download".format(client_cmd))
"""Run ``qpc report download`` with ``options`` and return output."""

report_insights = functools.partial(cli_command, "{} -v report insights".format(client_cmd))
"""Run ``qpc report insights`` with ``options`` and return output."""

report_aggregate = functools.partial(cli_command, "{} -v report aggregate".format(client_cmd))
"""Run ``qpc report aggregate`` with ``options`` and return output."""


def convert_ip_format(ipaddr):
    """Convert IP strings (for generating expected test results)."""
    # Expand CIDR to a formatted list of IPs
    if "/" in ipaddr:
        network = ipaddress.ip_network(ipaddr, strict=False)
        ipaddr = '",\r\n        "'.join(str(ip) for ip in network.hosts())
    # Expand Ansible-style range
    elif re.search(r"\[\d+:\d+\]", ipaddr):
        match = re.match(r"(.*)\[(\d+):(\d+)\]", ipaddr)
        if match:
            base_ip, start, end = match.groups()
            start, end = int(start), int(end)
            expanded_ips = [f"{base_ip}{i}" for i in range(start, end + 1)]
            ipaddr = '",\r\n        "'.join(expanded_ips)
    # Convert space-separated IPs into formatted multi-line string
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
    logger.debug(CLI_DEBUG_MSG, command)
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
    logger.debug(CLI_DEBUG_MSG, command)
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
    logger.debug(CLI_DEBUG_MSG, command)
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
    assert options != {}
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
    assert options != {}
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


def scans_with_source_type(source_type):
    """Find scans created for sources of given type.

    Conceptually, this belongs to DataProvider. However, DataProvider is
    concerned with efficiently creating a data defined in settings - here, we
    are concerned with data that exists in Quipucords database. DataProvider
    could, and arguably should, be extended to cover this use case, but as of
    this comment, there's a single test that needs this. Test in question is
    run after upgrade and entities defined in settings may already exist, but
    DataProvider is not aware of them.
    """
    matching_scans = []
    all_scans = json.loads(cli_command("{} -v scan list".format(client_cmd)))
    for scan in all_scans:
        if any(source_type == source.get("source_type") for source in scan.get("sources", [])):
            matching_scans.append(scan)
    return matching_scans


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
    logger.debug(CLI_DEBUG_MSG, command)
    output, exitstatus = pexpect.run(command, encoding="utf8", withexitstatus=True)
    assert exitstatus == 0, output

    # now login to the server
    command = "{} server login --username {}".format(client_cmd, qpc_config.username)
    logger.debug(CLI_DEBUG_MSG, command)
    output, exitstatus = pexpect.run(
        command,
        encoding="utf8",
        events=[("Password: ", qpc_config.password + "\n")],
        withexitstatus=True,
    )
    assert exitstatus == 0, output
