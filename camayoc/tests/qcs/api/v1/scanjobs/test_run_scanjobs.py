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

import pytest

import requests

from camayoc import api, utils
from camayoc.config import get_config
from camayoc.constants import (
    QCS_BRMS_RAW_FACTS,
    QCS_EAP_RAW_FACTS,
    QCS_FUSE_RAW_FACTS,
    VCENTER_CLUSTER,
    VCENTER_DATA_CENTER,
    VCENTER_HOST,
)
from camayoc.exceptions import (
    ConfigFileNotFoundError,
    WaitTimeError,
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
    module_cleanup.append(src)
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
        cred_ids[cred['name']] = create_cred(cred, module_cleanup)
    for hostname, source in inventory.items():
        # create sources on server, and keep track of source ids for each scan
        # name of cred to cred id on server
        source_ids[hostname], expected_products = create_source(
            source,
            cred_ids,
            module_cleanup
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
        run_scan(scan, disabled_optional_products, cleanup=module_cleanup)
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


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_disabled_optional_products_facts(scan_info):
    """Test scan jobs from scans with disabled optional products.

    :id: 6f91ea5c-32b9-11e8-b467-0ed5f89f718b
    :description: Test that scan jobs of scans with disabled products
        are not gathering the raw_facts defined in the roles of the
        disabled products.
    :steps:
        1) Iterate over the scans and gather the disabled_optional_products
        2) For any scan that was defined with disabled_optional_products:
            a) Create a facts_to_ignore list composed of raw_facts for each
                disabled role
            b) Iterate through the inspection results fact dictionaries
            c) Assert that no facts that should be ignored are in the
                dictionaries
    :expectedresults: No facts are collected for disabled products
    """
    errors_found = []
    scan = get_scan_result(scan_info['name'])
    facts_to_ignore = []
    disabled_optional_products = scan_info.get('disabled_optional_products')
    if disabled_optional_products:
        # Build the list of facts that should not be in inspection results
        for product in disabled_optional_products.keys():
            if product == 'jboss_eap':
                facts_to_ignore += QCS_EAP_RAW_FACTS
            elif product == 'jboss_fuse':
                facts_to_ignore += QCS_FUSE_RAW_FACTS
            elif product == 'jboss_brms':
                facts_to_ignore += QCS_BRMS_RAW_FACTS
        # grab the inspection results of the scan
        inspection_results = \
            scan.get('inspection_results')
        for system in inspection_results:
            fact_dicts = system.get('facts')
            # grab the facts for each system
            for dictionary in fact_dicts:
                for fact in facts_to_ignore:
                    if fact in dictionary.values():
                        errors_found.append(
                            'Found fact {fact_name} that should have been '
                            'DISABLED on scan named {scan_name}'.format(
                                fact_name=fact,
                                scan_name=scan.get('name')))
    assert len(errors_found) == 0, '\n================\n'.join(errors_found)


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_disabled_optional_products(scan_info):
    """Test scan jobs from scans with disabled_optional_products.

    :id: 77aa1f0c-32be-11e8-b467-0ed5f89f718b
    :description: Test that scans created with disabled products
        retain the same disabled products when results are obtained
        from the api
    :steps: 1) Iterate over scans and gather disabled products
            2) If the scans have disabled products, grab the
                disabled_products that were returned in the scan results
            3) Check that each specified product has the same value
                after being returned from the api
    :expectedresults: The values for disabled products specified in the
        config file are the same as those returned from the api
    """
    scan = get_scan_result(scan_info['name'])
    errors_found = []
    # grab disabled products from config file
    specified_optional_products = scan_info.get('disabled_optional_products')
    if specified_optional_products:
        # grab disabled products from results
        returned_optional_products = \
            scan.get('scan_results').get('options').get(
                'disabled_optional_products')
        for product in specified_optional_products:
            if specified_optional_products[product] != \
                    returned_optional_products[product]:
                errors_found.append(
                    'The product {product_name} should have been set to '
                    '{product_status} but was returned with a value of '
                    '{returned_status} on scan named {scan_name}'.format(
                        product_name=product,
                        product_status=specified_optional_products[product],
                        returned_status=returned_optional_products[product],
                        scan_name=scan.get('name')))
    assert len(errors_found) == 0, '\n================\n'.join(errors_found)


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_products_found_deployment_report(scan_info):
    """Test that products reported as present are correct for the source.

    :id: d5d424bb-8183-4b60-b21a-1b4ed1d879c0
    :description: Test that products indicated as present are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that any products marked as present are expected to be found
           as is listed in the configuration file for the source.
    :expectedresults: There are inspection results for each source we scanned
        and any products found are correctly identified.
    """
    result = get_scan_result(scan_info['name'])
    report_id = result['report_id']
    report = api.Client().get(
        'reports/{}/deployments'.format(report_id)).json().get('report')
    errors_found = []
    for entity in report:
        all_found_products = []
        present_products = []
        for product in entity.get('products'):
            name = ''.join(product['name'].lower().split())
            if product['presence'] == 'present':
                present_products.append(name)
            if product['presence'] in ['present', 'potential']:
                all_found_products.append(name)
        for source_to_product_map in result['expected_products']:
            src_id = list(source_to_product_map.keys())[0]
            hostname = result['source_id_to_hostname'][src_id]
            ex_products = source_to_product_map[src_id]
            expected_product_names = [
                prod for prod in ex_products.keys() if prod != 'distribution']
            if src_id in [s['id'] for s in entity['sources']]:
                # We assert that products marked as present are expected
                # We do not assert that products marked as potential must
                # actually be on server
                unexpected_products = []
                for prod_name in present_products:
                    # Assert that products marked "present"
                    # Are actually expected on machine
                    if prod_name not in expected_product_names:
                        unexpected_products.append(prod_name)
                # after inpsecting all found products,
                # raise assertion error for all unexpected products
                if len(unexpected_products) > 0:
                    errors_found.append(
                        'Found {found_products} but only expected to find\n'
                        '{expected_products} on {host_found_on}.\n'
                        'All information about the entity was as follows\n'
                        '{entity_info}'
                        .format(
                            found_products=unexpected_products,
                            expected_products=expected_product_names,
                            host_found_on=hostname,
                            entity_info=pformat(entity)
                        )
                    )
    assert len(errors_found) == 0, (
        'Found {num} unexpected products!\n'
        'Errors are listed below: {errors}'.format(
            num=len(errors_found),
            errors='\n\n======================================\n\n'.join(
                errors_found
            ),
        )
    )


@pytest.mark.parametrize(
    'scan_info', scan_info(), ids=utils.name_getter)
def test_OS_found_deployment_report(scan_info):
    """Test that OS identified are correct for the source.

    :id: 0b16331c-2431-498a-9e84-65b3d66e4001
    :description: Test that OS type and version are correctly
        identified.
    :steps:
        1) Request the json report for the scan.
        2) Assert that the OS identified is expected to be found
           as is listed in the configuration file for the source.
    :expectedresults: There are inspection results for each source we scanned
        and the operating system is correctly identified.
    """
    result = get_scan_result(scan_info['name'])
    report_id = result['report_id']
    report = api.Client().get(
        'reports/{}/deployments'.format(report_id)).json().get('report')
    errors_found = []
    for entity in report:
        for source_to_product_map in result['expected_products']:
            src_id = list(source_to_product_map.keys())[0]
            hostname = result['source_id_to_hostname'][src_id]
            ex_products = source_to_product_map[src_id]
            expected_distro = ex_products['distribution'].get('name', '')
            expected_version = ex_products['distribution'].get('version', '')
            found_distro = entity.get('os_name')
            found_version = entity.get('os_version')
            if src_id in [s['id'] for s in entity['sources']]:
                # We assert that the expected distro's name is at least
                # contained in the found name.
                # For example, if "Red Hat" is listed in config file,
                # It will pass if "Red Hat Enterprise Linux Server" is found
                if expected_distro not in found_distro:
                    errors_found.append(
                        'Expected OS named {0} for source {1} but'
                        'found OS named {2}'.format(
                            expected_distro,
                            hostname,
                            found_distro,
                        )
                    )
                # We assert that the expected distro's version is at least
                # contained in the found version.
                # For example, if "6.9" is listed in config file,
                # It will pass if "6.9 (Santiago)" is found
                if expected_version not in found_version:
                    errors_found.append(
                        'Expected OS version {0} for source {1} but'
                        'found OS version {2}'.format(
                            expected_version,
                            hostname,
                            found_version,
                        )
                    )

    assert len(errors_found) == 0, (
        'Found {num} unexpected OS names and/or versions!\n'
        'Errors are listed below: {errors}'.format(
            num=len(errors_found),
            errors='\n\n======================================\n\n'.join(
                errors_found
            ),
        )
    )
