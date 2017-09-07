# coding=utf-8
"""Tests for ``rho scan`` commands.

These tests are parametrized on the profiles listed in the config file. If scan
is successful, all facts will be validated before test fails, and then all
failed facts will be reported with associated host.

:caseautomation: automated
:casecomponent: scan
:caseimportance: high
:requirement: RHO
:testtype: functional
:upstream: yes
"""

import csv
import os
import pexpect
import pytest
from io import BytesIO

from camayoc import config
from camayoc.tests.rho.utils import auth_add, input_vault_password
from camayoc.exceptions import ConfigFileNotFoundError


def profiles():
    """Gather profiles from config file."""
    try:
        profs = config.get_config()['rho']['profiles']
    except ConfigFileNotFoundError:
        profs = []
    return profs


# The test will execute once per profile.
@pytest.mark.parametrize('profile', profiles())
def test_scan(isolated_filesystem, profile):
    """Scan the machines listed in profile.

    Then test facts for each host in profile.

    :id: 6ee18084-86db-45ea-8fdd-59fed5639170
    :description: Scan a machine and test collected facts.
    :steps:
            1) Run ``rho scan --profile <profile> --reportfile <reportfile>``
            2) Validate collected facts against known facts in config file
    :expectedresults:
        A scan is performed and a report with valid facts are
        generated.
    """
    cfg = config.get_config()

    for auth in cfg['rho']['auths']:
        auth_add({
            'name': auth['name'],
            'username': auth['username'],
            'sshkeyfile': auth['sshkeyfile'],
        })

    auths = ' '.join(item for item in profile['auths'])
    hosts = ' '.join(item for item in profile['hosts'])
    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(profile['name'], auths, hosts)
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect(
        'Profile "{}" was added'.format(profile['name'])) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    reportfile = '{}-report.csv'.format(profile['name'])
    rho_scan = pexpect.spawn(
        'rho scan --profile {} --reportfile {}'
        .format(profile['name'], reportfile),
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

    # we will collect errors in scanned facts and report at end of test on the
    # results if collected facts do not match expected values.
    scan_errors = []
    with open(reportfile) as csvfile:
        scan_results = csv.DictReader(csvfile)
        # each row corresponds to a scanned host
        for row in scan_results:
            known_facts = {}
            for host in cfg['rho']['hosts']:
                # find the facts for the scanned host we are inspecting
                if host['ip'] == row['connection.host']:
                    known_facts = host['facts']
                    break
            for fact in known_facts.keys():
                try:
                    assert (str(known_facts[fact]) in str(row[fact]))
                except AssertionError:
                    msg = 'Test failed on host {} in profile {}. \
                           Scan found {} = {} instead of {}.'.format(
                        host['ip'],
                        profile['name'],
                        fact,
                        row[fact],
                        known_facts[fact],
                    )
                    scan_errors.append(msg)
    if len(scan_errors) != 0:
        msg = '\n'.join(e for e in scan_errors)
        raise AssertionError(msg)
