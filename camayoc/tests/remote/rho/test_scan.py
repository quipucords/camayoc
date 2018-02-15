# coding=utf-8
"""Tests for ``rho scan`` commands.

These tests are parametrized on the profiles listed in the config file. If scan
is successful, all facts will be validated before test fails, and then all
failed facts will be reported with associated host.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""
import csv
import itertools
import os
import ssl
import time
from io import BytesIO

import pexpect
import pytest
from pyVim.connect import SmartConnect, Disconnect

from camayoc import cli, utils
from camayoc.config import get_config
from camayoc.constants import (
    CONNECTION_PASSWORD_INPUT,
    RHO_ALL_FACTS,
    VCENTER_CLUSTER,
    VCENTER_DATA_CENTER,
    VCENTER_HOST,
)
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.tests.rho.utils import auth_add, input_vault_password


SCAN_RESULTS = {}
"""Cache for the scan results returned by :func:get_scan_result."""


def is_live(client, server, num_pings=10):
    """Test if server responds to ping.

    Returns true if server is reachable, false otherwise.
    """
    client.response_handler = cli.echo_handler
    ping = client.run(('ping', '-c', num_pings, server))
    return ping.returncode == 0


def wait_until_live(servers, timeout=60):
    """Wait for servers to be live.

    For each server in the "servers" list, verify if it is reachable.
    Keep trying until a connection is made for all servers or the timeout
    limit is reached.

    If the timeout limit is reached, we exit even if there are unreached hosts.
    This means tests could fail with "No auths valid for this profile" if every
    host in the profile is unreachable. Otherwise, if there is at least one
    valid host, the scan will go on and only facts about reached hosts will be
    tested.

    `See rho issue #302 <https://github.com/quipucords/rho/issues/302>`_
    """
    system = cli.System(hostname='localhost', transport='local')
    client = cli.Client(system)

    unreached = servers
    while unreached and timeout > 0:
        unreached = [host for host in unreached if not is_live(client, host)]
        time.sleep(10)
        timeout -= 10


@pytest.fixture(scope='module')
def vcenter_client():
    """Create a vCetner client.

    Get the client confifuration from environment variables and Camayoc's
    configuration file in this order. Raise a KeyError if can't find the
    expecting configuration.

    The expected environment variables are VCHOSTNAME, VCUSER and VCPASS for
    vcenter's hostname, username and password respectively.

    The configuration in the Camayoc's configuration file should be as the
    following::

        vcenter:
          hostname: vcenter.domain.example.com
          username: gandalf
          password: YouShallNotPass

    The vcenter config can be mixed by using both environement variables and
    the configuration file but environment variable takes precedence.
    """
    config = get_config()
    vcenter_host = os.getenv('VCHOSTNAME', config['vcenter']['hostname'])
    vcenter_user = os.getenv('VCUSER', config['vcenter']['username'])
    vcenter_pwd = os.getenv('VCPASS', config['vcenter']['password'])

    try:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
        )
    except ssl.SSLError:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_pwd,
            sslContext=ssl._create_unverified_context(),
        )
    yield c
    Disconnect(c)


@pytest.fixture(scope='module', autouse=True)
def isolated_filesystem():
    """Override isolated_filesystem fixture updating the scope."""
    with utils.isolated_filesystem():
        yield


def scan_machine(machine, auth, profile_name):
    """Scan a machine and return its report file path.

    Helper to the scan_machines fixtures to scan a single machine and return
    its report file path if the scan can complete.

    Any unexpected behavior will raise an AssertionError.
    """
    rho_profile_add = pexpect.spawn(
        'rho profile add --name {} --auth {} --hosts {}'
        .format(profile_name, auth['name'], machine['ipv4'])
    )
    input_vault_password(rho_profile_add)
    assert rho_profile_add.expect(
        'Profile "{}" was added'.format(profile_name)) == 0
    assert rho_profile_add.expect(pexpect.EOF) == 0
    rho_profile_add.close()
    assert rho_profile_add.exitstatus == 0

    reportfile = '{}-report.csv'.format(profile_name)
    rho_scan = pexpect.spawn(
        'rho scan --profile {} --reportfile {} --facts all'
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
    return reportfile


@pytest.fixture(scope='module', autouse=True)
def scan_machines(vcenter_client, isolated_filesystem):
    """Scan all machines caching the results.

    Scan each machine found in the configuration's file inventory using each
    auth defined in the same file.

    Cache the report path of each scan or ``None`` if the scan can't be
    completed.

    The expected configuration in the Camayoc's configuration file is as
    follows::

        inventory:
          - hostname: sample-none-rhel-5-vc
            ipv4: 10.10.10.1
            hypervisor: vcenter
            distribution:
                name: rhel
                version: '5.9'
            products: {}
          - hostname: sample-none-rhel-6-vc
            ipv4: 10.10.10.2
            hypervisor: vcenter
            distribution:
                name: rhel
                version: '6.9'
            products: {}

        credentials:
            - name: root
              sshkeyfile: /path/to/.ssh/id_rsa
              username: root
              type: network

            - name: admin
              sshkeyfile: /path/to/.ssh/id_rsa
              username: admin
              type: network

    If you need rho to skip using a network credential, add the field as
    follows:

            - name: admin
              sshkeyfile: /path/to/.ssh/id_rsa
              username: admin
              type: network
              rho: false

    In the sample configuration file above will be performed four scans, one
    for each auth and machine combination.
    """
    config = get_config()
    auths = [auth for auth in config['credentials']
             if auth['type'] == 'network' and auth.get('rho', True)]
    inventory = {
        machine['hostname']: machine for machine in config['inventory']
        if machine['hypervisor'] == 'vcenter'
    }
    if not auths or not inventory:
        raise ValueError(
            'Make sure to have credentials and inventory'
            ' items in the config file'
        )
    hostnames = [machine['hostname'] for machine in inventory.values()]
    host_folder = vcenter_client.content.rootFolder \
        .childEntity[VCENTER_DATA_CENTER].hostFolder
    host = host_folder.childEntity[VCENTER_CLUSTER].host[VCENTER_HOST]
    vms = [
        vm for vm in host.vm
        if vm.name in hostnames
    ]
    for auth in auths:
        if auth.get('sshkeyfile'):
            auth_add({
                'name': auth['name'],
                'username': auth['username'],
                'sshkeyfile': auth['sshkeyfile'],
            })
        elif auth.get('password'):
            auth_add(
                {
                    'name': auth['name'],
                    'username': auth['username'],
                    'password': None,
                },
                [(
                    CONNECTION_PASSWORD_INPUT,
                    auth['password']
                )],
            )
    chunk_size = 5
    chunks = [vms[i:i+chunk_size] for i in range(0, len(vms), chunk_size)]
    for chunk in chunks:
        machines_to_wait = []
        for vm in chunk:
            if vm.runtime.powerState == 'poweredOff':
                vm.PowerOnVM_Task()
                machines_to_wait.append(inventory[vm.name])
        wait_until_live(machines_to_wait)
        for vm in chunk:
            if vm.runtime.powerState == 'poweredOn':
                machine = inventory[vm.name]
                for auth in auths:
                    profile_name = machine['hostname'] + '-' + auth['name']
                    try:
                        result = scan_machine(machine, auth, profile_name)
                    except (AssertionError, pexpect.exceptions.EOF) as err:
                        with open(profile_name, 'w') as handler:
                            handler.write(str(err))
                        result = None
                    SCAN_RESULTS[profile_name] = result

                vm.PowerOffVM_Task()


def scan_permutations():
    """Generate a tuple of hostname and auth matching expected scans."""
    try:
        config = get_config()
        auths = [auth for auth in config['credentials']
                 if auth['type'] == 'network' and auth.get('rho', True)]
        inventory = config['inventory']
        return list(itertools.product(inventory, auths))
    except (ConfigFileNotFoundError, KeyError):
        return []


def get_permutation_id(param):
    """Return a string representation for each  :func:`test_scan` parameter."""
    return param.get('name') or param.get('hostname')


@pytest.mark.parametrize(
    'machine,auth', scan_permutations(), ids=get_permutation_id)
def test_scan(machine, auth):
    """Test each scan report.

    :id: d9eb29bd-1b61-421a-b680-f494e868b11e
    :description: Test if the scan produced the expected report for a given
        auth and machine.
    :steps: For each machine in the inventory perform one scan per available
        auth.
    :expectedresults: The generate report must have the expected fact values.
    """
    profile_name = machine['hostname'] + '-' + auth['name']
    result = SCAN_RESULTS[profile_name]
    if result is None:
        with open(profile_name) as handler:
            result = handler.read()
        pytest.fail(
            'Was not able to scan {0[hostname]} using the auth {1[name]}.\n'
            'Machine object: {0}\n\nAuth object: {1}\n\nException: {2}'
            .format(machine, auth, result)
        )

    with open(result) as f:
        fieldnames = csv.DictReader(f).fieldnames
    assert sorted(fieldnames) == sorted(RHO_ALL_FACTS)
