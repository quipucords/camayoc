# coding=utf-8
"""Pytest customizations and fixtures for tests to execute on remote hosts."""

import csv
import os
import pexpect
import pytest
import tempfile
import shutil
from io import BytesIO

from camayoc import config
from camayoc.tests.rho.utils import auth_add, input_vault_password
from camayoc.utils import _XDG_ENV_VARS

def pytest_generate_tests(metafunc):
    if hasattr(metafunc.function, 'facts_needed'):
        # this grabs the parameters handed to the pytest.mark.parametrize
        # associated with the function that is marked 'facts_needed'
        profiles_to_scan = metafunc.function.parametrize
        # now we will pass those parameters to another function
        # to perform the scan and collect all testable facts.
        # This will have the effect of the test being parametrized
        # on the facts, not the profiles, so a test will run
        # for each fact
        metafunc.function.parametrize = [testable_facts(profiles_to_scan)]


def testable_facts(profiles_to_scan):
    profiles_to_scan = profiles_to_scan.args[1]
    cfg = config.get_config()
    facts_to_test = []
    for profile in profiles_to_scan:
        cwd = os.getcwd()
        path = tempfile.mkdtemp()
        for envvar in _XDG_ENV_VARS:
            os.environ[envvar] = path
        os.chdir(path)
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
            # This is a fixture for tests that ensure scanned facts in a
            # successful scan are correct, not that we can scan, so we
            # will carry on.
            pass

        scan_results = []
        if os.path.isfile(reportfile):
            # open the report and collect the facts of interest, injecting
            # other useful information while we are at it.
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
                                    'profile': row['profile'],
                                    'auth': row['auth'],
                                    'scandir': path,
                                })
                        break
        for envvar in _XDG_ENV_VARS:
            os.environ[envvar] = ''
        os.chdir(cwd)
        try:
            shutil.rmtree(path)
        except (OSError, IOError):
            pass
    return pytest.mark.parametrize(
                            'fact',
                            facts_to_test,
                            ids=['{}-{}-{}-{}'.format(
                                fact['host'],
                                fact['profile'],
                                fact['auth'],
                                fact['fact']) for fact in facts_to_test])
