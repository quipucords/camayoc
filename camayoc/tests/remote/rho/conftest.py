# coding=utf-8
"""Pytest customizations and fixtures for tests to execute on remote hosts."""

import csv
import os
from io import BytesIO

import pexpect
import pytest

from camayoc import config
from camayoc.utils import isolated_filesystem
from camayoc.tests.rho.utils import auth_add, input_vault_password


def pytest_generate_tests(metafunc):
    """Do magic things with parameters.

    This function enables us to create custom marks and do special things to
    the parameters of fixtures based on the value of the marks.

    In particular, the marks that use this function are:

    .. code-block:: python

        @pytest.mark.facts_needed

    The `facts_needed` mark tells us to take the parameters, which should be
    profiles, to the test marked with this marker and pass them to the
    `testable_facts` function which will perform a scan for each profile passed
    to the original test. It will then, in turn, generate a list of facts for
    the test to be parametrized on. This has the effect of the test being
    parametrized on the facts, not the profiles.
    """
    if hasattr(metafunc.function, 'facts_needed'):
        # this grabs the parameters handed to the pytest.mark.parametrize
        # associated with the function that is marked 'facts_needed'
        profiles_to_scan = metafunc.function.parametrize
        # now we will pass those parameters to another function
        # to perform the scans and return a list of all testable facts.
        metafunc.function.parametrize = [testable_facts(profiles_to_scan)]


def testable_facts(profiles_to_scan):
    """Perform scans on each profile and return facts.

    This function will attempt to scan all profiles listed in config file. For
    those that are successful, facts will be returned so the test may be
    parametrized on them.

    Additional data about the facts like what host, profile, auth, actual and
    expected value are collected into a single dictionary with the scanned fact
    and passed to the test that is marked as follows:

    .. code-block:: python

        @pytest.mark.facts_needed
        @pytest.mark.parametrize('fact', profiles())

    """
    profiles_to_scan = profiles_to_scan.args[1]
    cfg = config.get_config()
    facts_to_test = []
    for profile in profiles_to_scan:
        with isolated_filesystem() as path:
            reportfile = '{}-report.csv'.format(profile['name'])
            try:
                for auth in cfg['rho']['auths']:
                    if auth['name'] in profile['auths']:
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

                rho_scan = pexpect.spawn(
                    'rho scan --profile {} --reportfile {} --facts all'
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
            except (AssertionError, pexpect.exceptions.EOF):
                # The scan failed for some reason.
                # We insert a fact that records that the scan failed
                # so we will see a test failure for this profile scan
                facts_to_test.append(
                    {
                        'fact': 'scan-performed',
                        'expected': True,
                        'actual': False,
                        'host': 'N/A',
                        'host-ip': 'N/A',
                        'profile': profile['name'],
                        'auth': profile['auths'],
                        'scandir': path,
                        'privileged': profile.get('privileged')
                    }
                )

            scan_results = []
            if os.path.isfile(reportfile):
                # open the report and collect the facts of interest, injecting
                # other useful information while we are at it.
                # We insert a fact that records that the scan succeeded
                # in producing a report so we will see a test success for this
                # profile scan
                facts_to_test.append(
                    {
                        'fact': 'scan-performed',
                        'expected': True,
                        'actual': True,
                        'host': 'N/A',
                        'host-ip': 'N/A',
                        'profile': profile['name'],
                        'auth': profile['auths'],
                        'scandir': path,
                        'privileged': profile.get('privileged')
                    }
                )
                with open(reportfile) as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        row['profile'] = profile['name']
                        row['auth'] = profile['auths']
                        scan_results.append(row)

                for row in scan_results:
                    known_facts = {}
                    for host in cfg['rho']['hosts']:
                        # find the facts for the scanned host we are inspecting
                        if host['ip'] == row.get('connection.host'):
                            known_facts = host['facts']
                            for fact in known_facts:
                                facts_to_test.append(
                                    {
                                        'fact': fact,
                                        'expected': known_facts.get(fact),
                                        'actual': row.get(fact),
                                        'host': host['hostname'],
                                        'host-ip': host['ip'],
                                        'profile': row['profile'],
                                        'auth': row['auth'],
                                        'scandir': path,
                                        'privileged': profile.get('privileged')
                                    }
                                )
                            break
    return pytest.mark.parametrize(
        'fact',
        facts_to_test,
        ids=['{}-{}-{}-{}'.format(
            fact['host-ip'],
            fact['profile'],
            fact['auth'],
            fact['fact']) for fact in facts_to_test])
