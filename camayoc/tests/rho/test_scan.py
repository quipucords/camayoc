# coding=utf-8
"""Tests for ``rho scan`` commands.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""
import csv
import os
import random
from io import BytesIO

import pexpect
import pytest

from camayoc import utils
from camayoc.constants import (
    RHO_CONNECTION_FACTS,
    RHO_DEFAULT_FACTS,
    RHO_JBOSS_ALL_FACTS,
    RHO_JBOSS_FACTS,
    RHO_RHEL_FACTS,
)
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
    assert os.path.isfile(reportfile), logfile
    with open(reportfile) as f:
        fieldnames = csv.DictReader(f).fieldnames
    assert sorted(fieldnames) == sorted(RHO_DEFAULT_FACTS)


@pytest.mark.parametrize('facts', ('all', 'default', 'jboss', 'rhel', 'file'))
def test_scan_with_facts(isolated_filesystem, facts):
    """Scan a machine and provide the list of facts to be scanned.

    :id: 014ad607-9c82-422d-8aa1-59f47aa065ea
    :description: Scan a machine and provide the list of facts to be scanned.
    :steps: Run ``rho scan --facts <facts> --profile <profile> --reportfile
        <reportfile>``
    :expectedresults: A scan is perfomed and the report file is generated with
        the specified facts.
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

    if facts == 'all':
        expected_facts = RHO_DEFAULT_FACTS + RHO_JBOSS_ALL_FACTS
    if facts == 'default':
        expected_facts = RHO_DEFAULT_FACTS
    elif facts == 'jboss':
        expected_facts = RHO_JBOSS_FACTS + RHO_CONNECTION_FACTS
    elif facts == 'rhel':
        expected_facts = RHO_RHEL_FACTS + RHO_CONNECTION_FACTS
    elif facts == 'file':
        # Remove the RHO_CONNECTION_FACTS which will be aways added
        expected_facts = list(
            set(RHO_DEFAULT_FACTS).difference(RHO_CONNECTION_FACTS))
        expected_facts = random.sample(
            expected_facts, random.randint(1, len(expected_facts)))
        facts = 'facts_file'
        with open(facts, 'w') as handler:
            for fact in expected_facts:
                handler.write(fact + '\n')
        # Include back the RHO_CONNECTION_FACTS
        expected_facts.extend(RHO_CONNECTION_FACTS)

    rho_scan = pexpect.spawn(
        'rho scan --facts {} --profile {} --reportfile {}'
        .format(facts, profile_name, reportfile),
        timeout=300,
    )
    input_vault_password(rho_scan)
    rho_scan.logfile = BytesIO()
    assert rho_scan.expect(pexpect.EOF) == 0
    logfile = rho_scan.logfile.getvalue().decode('utf-8')
    rho_scan.logfile.close()
    rho_scan.close()
    assert rho_scan.exitstatus == 0, logfile
    assert os.path.isfile(reportfile), logfile

    with open(reportfile) as f:
        fieldnames = csv.DictReader(f).fieldnames
    assert sorted(fieldnames) == sorted(expected_facts)
