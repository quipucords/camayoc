# coding=utf-8
"""Tests for ``rho scan`` commands.

:caseautomation: automated
:casecomponent: scan
:caseimportance: high
:requirement: RHO
:testtype: functional
:upstream: yes
"""
import os
from io import BytesIO

import pexpect

from camayoc import utils
from camayoc.tests.rho.utils import auth_add, input_vault_password


def test_scan(isolated_filesystem):
    """Scan one machine.

    :id: 5be9627b-ed2f-46f4-9439-193cc2cf6ec6
    :description: Scan a machine.
    :steps: Run ``rho scan --profile <profile> --reportfile <reportfile>``
    :expectedresults: A scan is perfomed and the report file is generated.
    """
    auth_name = utils.uuid4()
    profile_name = utils.uuid4()
    hosts = 'localhost'
    reportfile = utils.uuid4()
    auth_add({
        'name': auth_name,
        'username': os.environ['USER'],
        'sshkeyfile': os.path.join(os.environ['HOME'], '.ssh', 'id_rsa'),
    })

    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(profile_name, auth_name, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect(
        'Profile "{}" was added'.format(profile_name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    rho_scan = pexpect.spawn(
        'rho scan --profile {} --reportfile {}'
        .format(profile_name, reportfile),
        timeout=300,
    )
    input_vault_password(rho_scan)
    rho_scan.logfile = BytesIO()
    assert rho_scan.expect(pexpect.EOF) == 0
    logfile = rho_scan.logfile.getvalue().decode('utf-8')
    rho_scan.logfile.close()
    rho_scan.close()
    assert rho_scan.exitstatus == 0, logfile
    assert os.path.isfile(reportfile)
