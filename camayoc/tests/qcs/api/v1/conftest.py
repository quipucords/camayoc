"""Pytest customizations and fixtures for the quipucords tests."""
from pprint import pformat

import pytest

import requests

from camayoc.config import get_config

from camayoc.exceptions import (
    WaitTimeError,
)
from camayoc.constants import (
    VCENTER_CLUSTER,
    VCENTER_DATA_CENTER,
    VCENTER_HOST,
)
from camayoc.qcs_models import (
    Credential,
    Scan,
    ScanJob,
    Source,
)
from camayoc.tests.qcs.api.v1.utils import wait_until_state
from camayoc.tests.utils import wait_until_live


SCAN_DATA = {}
"""Cache to associate the named scans with their results."""


def create_cred(cred_info, session_cleanup):
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
    session_cleanup.append(c)
    return c._id


def create_source(source_info, cred_name_to_id_dict, session_cleanup):
    """Given info about source from config file, create it.

    :returns: A tuple containing the The id of the created source and a
        dictionary of the expected products from the config file.
    """
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
    expected_products = source_info.get('products', {})
    expected_products.update(
        {'distribution': source_info.get('distribution', {})})
    src.create()
    session_cleanup.append(src)
    return src._id, expected_products


def run_scan(scan, disabled_optional_products, cleanup,
             scan_type='inspect'):
    """Scan a machine and cache any available results.

    If errors are encountered, save those and they can be included
    in test results.
    """
    src_ids = scan['source_ids']
    scan_name = scan['name']
    SCAN_DATA[scan_name] = {
        'scan_id': None,       # scan id
        'scan_job_id': None,   # scan job id
        'final_status': None,  # Did the scan job contain any failed tasks?
        'scan_results': None,  # Number of systems reached, etc
        'report_id': None,     # so we can retrieve report
        'connection_results': None,  # details about connection scan
        'inspection_results': None,  # details about inspection scan
        'errors': [],
        'expected_products': scan['expected_products'],
        'source_id_to_hostname': scan['source_id_to_hostname'],
    }
    try:
        scan = Scan(source_ids=src_ids, scan_type=scan_type,
                    disabled_optional_products=disabled_optional_products)
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
        SCAN_DATA[scan_name]['inspection_results'] = \
            scanjob.inspection_results().json().get('results')
    except (requests.HTTPError, WaitTimeError) as e:
        SCAN_DATA[scan_name]['errors'].append('{}'.format(pformat(str(e))))


@pytest.fixture(scope='session', autouse=True)
def run_all_scans(vcenter_client, session_cleanup):
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
                  disabled_optional_products: {'jboss_fuse': True}
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
        cred_ids[cred['name']] = create_cred(cred, session_cleanup)
    for hostname, source in inventory.items():
        # create sources on server, and keep track of source ids for each scan
        # name of cred to cred id on server
        source_ids[hostname], expected_products = create_source(
            source,
            cred_ids,
            session_cleanup
        )
        for scan in scans:
            scan.setdefault('source_ids', [])
            scan.setdefault('expected_products', [])
            scan.setdefault('source_id_to_hostname', {})
            for source in scan['sources']:
                if hostname == source:
                    scan['source_ids'].append(source_ids[hostname])
                    scan['expected_products'].append(
                        {source_ids[hostname]: expected_products}
                    )
                    scan['source_id_to_hostname'].update(
                        {source_ids[hostname]: hostname}
                    )
    for scan in scans:
        # grab the disabled products if they exist, otherwise {}
        disabled_optional_products = scan.get('disabled_optional_products', {})
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
        run_scan(scan, disabled_optional_products, cleanup=session_cleanup)
        for vm in vcenter_vms:
            if vm.runtime.powerState == 'poweredOn':
                vm.PowerOffVM_Task()
