# coding=utf-8
"""Tests for  quipucords scans and reports.

These tests are parametrized on the inventory listed in the config file.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: quipucords
:testtype: functional
:upstream: yes
"""
from pprint import pformat

import requests
import pytest

from camayoc import utils
from camayoc.qcs_models import (
    Credential,
    Source,
    Scan,
    ScanJob,
)
from camayoc.config import get_config
from camayoc.constants import (
    VCENTER_CLUSTER,
    VCENTER_DATA_CENTER,
    VCENTER_HOST,
)
from camayoc.exceptions import (
    ConfigFileNotFoundError,
    WaitTimeError,
)
from camayoc.tests.utils import wait_until_live
from camayoc.tests.qcs.api.v1.utils import wait_until_state


SCAN_DATA = {}
"""Cache to associate the named scans with their results."""


def create_cred(cred_info, module_cleanup):
    """Given info about cred from config file, create it and return id."""
    c = Credential(
        cred_type=cred_info['type'],
        username=cred_info['username'],
    )
    if cred_info.get('sshkeyfile'):
        c.ssh_keyfile = cred_info['sshkeyfile']
    else:
        c.password = cred_info['password']
    c.create()
    module_cleanup.append(c)
    return c._id


def create_source(source_info, cred_name_to_id_dict, module_cleanup):
    """Given info about source from config file, create it and return id."""
    cred_ids = [value for key, value in cred_name_to_id_dict.items(
    ) if key in source_info['credentials']]
    host = source_info.get('ipv4') if source_info.get(
        'ipv4') else source_info.get('hostname')
    src = Source(
        source_type=source_info.get('type', 'network'),
        hosts=[host],
        credential_ids=cred_ids,
        options=source_info.get('options')
    )
    src.create()
    module_cleanup.append(src)
    return src._id


def run_scan(src_ids, scan_name, cleanup, scan_type='inspect'):
    """Scan a machine and cache any available results.

    If errors are encountered, save those and they can be included
    in test results.
    """
    SCAN_DATA[scan_name] = {
        'scan_id': None,       # scan id
        'scan_job_id': None,   # scan job id
        'final_status': None,  # Did the scan job contain any failed tasks?
        'scan_results': None,  # Number of systems reached, etc
        'report_id': None,     # so we can retrieve report
        'connection_results': None,  # details about connection scan
        'inspection_results': None,  # details about inspection scan
        'errors': [],
    }
    try:
        scan = Scan(source_ids=src_ids, scan_type=scan_type)
        TIMEOUT = 500 * len(src_ids)
        scan.create()
        cleanup.append(scan)
        scanjob = ScanJob(scan_id=scan._id)
        scanjob.create()
        SCAN_DATA[scan_name]['scan_id'] = scan._id
        wait_until_state(scanjob, timeout=TIMEOUT, state='stopped')
        SCAN_DATA[scan_name]['final_status'] = scanjob.status()
        SCAN_DATA[scan_name]['scan_results'] = scanjob.read().json()
        SCAN_DATA[scan_name]['report_id'] = scanjob.read(
        ).json().get('report_id')
        SCAN_DATA[scan_name]['task_results'] = scanjob.read(
        ).json().get('tasks')
    except (requests.HTTPError, WaitTimeError) as e:
        SCAN_DATA[scan_name]['errors'].append('{}'.format(pformat(str(e))))


@pytest.fixture(scope='module', autouse=True)
def run_all_scans(vcenter_client, module_cleanup):
    """Run all configured scans caching the report id associated with each.

    Run each scan defined in the ``qcs`` section of the configuration file.

    Cache the report id of the scan, associating it with its scan.

    The expected configuration in the Camayoc's configuration file is as
    follows::

        qcs:
        # other needed qcs config data
        #
        # specific for scans:
            - scans:
                - name: network-vcenter-sat-mix
                  sources:
                      - sample-none-rhel-5-vc
                      - sample-sat-6
                      - sample-vcenter
        inventory:
          - hostname: sample-none-rhel-5-vc
            ipv4: 10.10.10.1
            hypervisor: vcenter
            distribution:
                name: rhel
                version: '5.9'
            products: {}
            credentials:
                - root
          - hostname: sample-sat-6
            type: 'vcenter'
            options:
                ssl_cert_verify: false
                satellite_version: '6.2'
            credentials:
                - sat6_admin
          - hostname: sample-vcenter
            type: 'vcenter'
            credentials:
                - vcenter_admin

        credentials:
            - name: root
              sshkeyfile: /path/to/.ssh/id_rsa
              username: root
              type: network

            - name: sat6_admin
              password: foo
              username: admin
              type: satellite

            - name: vcenter_admin
              password: foo
              username: admin
              type: vcenter

    In the sample configuration file above, one machine will be turned on,
    and one scan will be run against the three sources each created with
    their own credential.
    """
    config = get_config()
    creds = config['credentials']
    scans = config.get('qcs', {}).get('scans', [])
    if scans == []:
        # if no scans are defined, no need to go any further
        return
    inventory = {
        machine['hostname']: machine for machine in config['inventory']
    }
    vcenter_inventory = {
        machine['hostname']: machine for machine in config['inventory']
        if machine.get('hypervisor') == 'vcenter'
    }
    if not creds or not inventory:
        raise ValueError(
            'Make sure to have credentials and inventory'
            ' items in the config file'
        )
    vcenter_hostnames = list(vcenter_inventory.keys())
    host_folder = vcenter_client.content.rootFolder \
        .childEntity[VCENTER_DATA_CENTER].hostFolder
    host = host_folder.childEntity[VCENTER_CLUSTER].host[VCENTER_HOST]
    cred_ids = {}
    source_ids = {}
    for cred in creds:
        # create creds on server
        # create dict that associates the name of the cred to the cred id
        cred_ids[cred['name']] = create_cred(cred, module_cleanup)
    for hostname, source in inventory.items():
        # create sources on server, and keep track of source ids for each scan
        # name of cred to cred id on server
        source_ids[hostname] = create_source(source, cred_ids, module_cleanup)
        for scan in scans:
            for source in scan['sources']:
                if hostname == source:
                    scan.setdefault(
                        'source_ids', []).append(
                        source_ids[hostname])
    for scan in scans:
        # update the sources dict of each item in the scans list with the
        # source id if hosts are marked as being hosted on vcenter, turn them
        # on. then wait until they are live
        # then run the scan, caching the report id associated with the scan
        # and finally turn the managed machines off.
        vcenter_vms = [
            vm for vm in host.vm
            if (vm.name in vcenter_hostnames) and (vm.name in scan['sources'])
        ]
        machines_to_wait = []
        for vm in vcenter_vms:
            if vm.runtime.powerState == 'poweredOff':
                vm.PowerOnVM_Task()
                machines_to_wait.append(inventory[vm.name])
        wait_until_live(machines_to_wait, timeout=120)
        # now all host should be live and we can run the scan
        # all results will be saved in global cache
        # if errors occur, they will be saved but scanning will go on
        run_scan(scan['source_ids'], scan['name'], cleanup=module_cleanup)
        for vm in vcenter_vms:
            if vm.runtime.powerState == 'poweredOn':
                vm.PowerOffVM_Task()


def scan_info():
    """Generate list of scan dict objects found in config file."""
    try:
        return get_config().get('qcs', {}).get('scans', [])
    except (ConfigFileNotFoundError, KeyError):
        return []


def get_scan_result(scan_name):
    """Collect scan results from global cache.

    Raise an error if no results are available, because this means the scan
    was not even attempted.
    """
    result = SCAN_DATA.get(scan_name)
    if result is None:
        raise RuntimeError(
            'Absolutely no results available for scan named {scan_name},\n'
            'because no scan was even attempted.\n'.format(
                scan_name=scan_info['name'])
        )
    return result


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_scan_complete(scan_info):
    """Test that each scan completed without failures.

    :id: 4e7a608e-a18d-48db-b263-a0d5474385dd
    :description: Test if the scan completed.
    :steps: Check the final status of the scan.
    :expectedresults: Scans should complete and report their finished status.
    """
    result = get_scan_result(scan_info['name'])
    if result['final_status'] != 'completed':
        raise AssertionError(
            'Scan did not complete. Its final status was {status}.\n'
            ' A scan will be reported as failed if there were unreachable\n'
            ' hosts. Any additional errors encountered are listed here: \n'
            '{errors}\n'.format(
                status=result['final_status'],
                errors='\n'.join(result['errors']),
            )
        )


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_scan_task_results(scan_info):
    """Test the scan task results of each scan.

    :id: 8087fdc9-6626-476a-a11a-4783cbf501a0
    :description: Test the connection results of the scan
    :steps:
        1) Iterate over sources that we have connection results for.
        2) Inspect server arithmetic regarding number of systems scanned
    :expectedresults: There are task results for each source we scanned
       and we get an accurate count of how many were reached and how many
       failed for all tasks.
    """
    result = get_scan_result(scan_info['name'])
    task_results = result['task_results']
    for task in task_results:
        # assert arithmetic around number of systems scanned adds up
        # this has been broken in the past
        sys_count = task['systems_count']
        num_failed = task['systems_failed']
        num_scanned = task['systems_scanned']
        assert num_scanned == sys_count - num_failed
