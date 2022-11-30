import json
import os
import re

import pexpect

from camayoc import utils
from camayoc.constants import MASKED_TOKEN_OUTPUT
from camayoc.constants import TOKEN_INPUT
from camayoc.tests.qpc.cli.test_credentials import generate_show_output as show_cred_output
from camayoc.tests.qpc.cli.test_sources import generate_show_output as show_source_output
from camayoc.tests.qpc.cli.utils import clear_all_entities
from camayoc.tests.qpc.cli.utils import cred_add_and_check
from camayoc.tests.qpc.cli.utils import cred_show_and_check
from camayoc.tests.qpc.cli.utils import get_ocp_config_info
from camayoc.tests.qpc.cli.utils import report_detail
from camayoc.tests.qpc.cli.utils import scan_add_and_check
from camayoc.tests.qpc.cli.utils import scan_job
from camayoc.tests.qpc.cli.utils import scan_show_and_check
from camayoc.tests.qpc.cli.utils import scan_start
from camayoc.tests.qpc.cli.utils import source_show
from camayoc.tests.qpc.cli.utils import source_show_and_check
from camayoc.tests.qpc.cli.utils import wait_for_scan
from camayoc.utils import client_cmd


ocp_config = get_ocp_config_info()


def check_if_discovery_was_deployed(list_projects):
    """Check if discovery can be found in deployed projects."""
    discovery_found = False
    for project in list_projects:
        if project.get("name", "") == "discovery":
            discovery_found = True
            break
    return discovery_found


def test_end_to_end_cli_ocp(qpc_server_config):
    """End-to-end test for ocp instance with known deployed project using cli route."""
    # ocp cred tests
    # adding cred
    cred_name = "ocp_cred"
    cred_add_and_check(
        {"name": cred_name, "token": None, "type": "openshift"},
        [(TOKEN_INPUT, utils.uuid4())],
    )
    # editing cred
    qpc_cred_edit = pexpect.spawn("{} cred edit --name={} --token".format(client_cmd, cred_name))
    assert qpc_cred_edit.expect(TOKEN_INPUT) == 0
    qpc_cred_edit.sendline(ocp_config["token"])
    assert qpc_cred_edit.expect('Credential "{}" was updated'.format(cred_name)) == 0
    assert qpc_cred_edit.expect(pexpect.EOF) == 0
    qpc_cred_edit.close()
    assert qpc_cred_edit.exitstatus == 0

    # checking for saved cred
    cred_show_and_check(
        {"name": cred_name},
        show_cred_output(
            {"auth_token": MASKED_TOKEN_OUTPUT, "cred_type": "openshift", "name": cred_name}
        ),
    )

    # ocp source tests
    # adding source
    source_name = "ocp_source"
    hosts = ocp_config["hosts"]

    qpc_source_add = pexpect.spawn(
        "{} source add --name {} --cred {} --hosts {} --ssl-cert-verify false --type openshift".format(
            client_cmd, source_name, cred_name, "127.0.0.1"
        )
    )
    assert qpc_source_add.expect('Source "{}" was added'.format(source_name)) == 0
    assert qpc_source_add.expect(pexpect.EOF) == 0
    qpc_source_add.close()
    assert qpc_source_add.exitstatus == 0

    # editing source
    qpc_source_edit = pexpect.spawn(
        "{} source edit --name {} --hosts {}".format(client_cmd, source_name, hosts)
    )
    assert qpc_source_edit.expect('Source "{}" was updated'.format(source_name)) == 0
    assert qpc_source_edit.expect(pexpect.EOF) == 0
    qpc_source_edit.close()
    assert qpc_source_edit.exitstatus == 0

    # checking for saved source
    source_show_and_check(
        {"name": source_name},
        show_source_output(
            {
                "cred_name": cred_name,
                "hosts": hosts,
                "name": source_name,
                "options": {"ssl_cert_verify": "false"},
                "port": 6443,
                "source_type": "openshift",
            }
        ),
    )

    # ocp scan tests
    # adding a scan
    scan_name = "ocp_scan"
    scan_add_and_check({"name": scan_name, "sources": source_name})

    # checking for saved scan
    source_output = source_show({"name": source_name})
    source_output = json.loads(source_output)

    expected_result = {
        "id": "TO_BE_REPLACED",
        "name": scan_name,
        "options": {"max_concurrency": 25},
        "scan_type": "inspect",
        "sources": [{"id": source_output["id"], "name": source_name, "source_type": "openshift"}],
    }

    scan_show_and_check(scan_name, expected_result)

    # scan ocp source
    result = scan_start({"name": scan_name})
    match = re.match(r'Scan "(\d+)" started.', result)
    assert match is not None
    scan_job_id = match.group(1)
    wait_for_scan(scan_job_id, timeout=1800)
    result = scan_job({"id": scan_job_id})
    assert result["status"] == "completed"

    # check for report details
    report_id = 20
    assert report_id is not None
    output_file = "details.json"
    report = report_detail({"json": None, "output-file": output_file, "report": report_id})
    with open(output_file) as report_data:
        report = json.load(report_data)
        source_list = report["sources"]
        assert source_list != []
        list_projects = source_list[0]["facts"]
        discovery_found = check_if_discovery_was_deployed(list_projects)
        assert discovery_found
    os.remove(output_file)

    # clear scans, sources and creds
    clear_all_entities()
