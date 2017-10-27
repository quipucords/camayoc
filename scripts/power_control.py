# coding: utf-8
"""Turn on or off all vcenter machines.

Given a vcenter host and credentials to that host either on the command line or
in the standard camayoc config file, turn on or off all machines. For details
on invocation, run this script with the -h or --help flag.

Example of a valid 'vcenter' section of a camayoc config file:

    vcenter:
        username: 'user'
        password: 'password'
        hostname: 'vcenter.example.com'
"""

import argparse
import ssl
import yaml

from pyVim.connect import SmartConnect, Disconnect

from camayoc import config
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.constants import (
    VCENTER_DATA_CENTER,
    VCENTER_CLUSTER,
    VCENTER_HOST as VCENTER_HOST_INDX,
)

BASE_CONFIG = """
vcenter:
    username: 'user'
    password: 'password'
    hostname: 'vcenter.example.com'
"""


def get_config():
    """Gather existing config file or create one.

    If a config file is found by camayoc, use that.
    Otherwise, use BASE_CONFIG.
    """
    try:
        cfg = config.get_config()
    except ConfigFileNotFoundError:
        cfg = yaml.load(BASE_CONFIG)

    return cfg


def power_control(VCENTER_HOST,
                  VCENTER_USER,
                  VCENTER_PASSWORD,
                  VCENTER_ACTION):
    """Connect to vcenter and perform action on all sonar machines."""
    try:
        c = SmartConnect(
            host=VCENTER_HOST,
            user=VCENTER_USER,
            pwd=VCENTER_PASSWORD,
        )
    except ssl.SSLError:
        c = SmartConnect(
            host=VCENTER_HOST,
            user=VCENTER_USER,
            pwd=VCENTER_PASSWORD,
            sslContext=ssl._create_unverified_context(),
        )

    dc = c.content.rootFolder.childEntity[VCENTER_DATA_CENTER]
    vms = dc.hostFolder.childEntity[VCENTER_CLUSTER].host[VCENTER_HOST_INDX].vm

    for vm in vms:
        if vm.name.startswith('sonar-'):
            if VCENTER_ACTION == 'ON':
                if vm.runtime.powerState == 'poweredOff':
                    vm.PowerOnVM_Task()
            if VCENTER_ACTION == 'OFF':
                if vm.runtime.powerState == 'poweredOn':
                    vm.PowerOffVM_Task()

    Disconnect(c)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='The vcenter hostname.')
    parser.add_argument(
        '--host ',
        required=False,
        default=None,
        action='store',
        dest='VCENTER_HOST',
        type=str,
        help=('This is the hostname where you would log into vcenter from a'
              ' browser')
    )
    parser.add_argument(
        '--user ',
        required=False,
        default=None,
        action='store',
        dest='VCENTER_USER',
        type=str,
        help='Username on vcenter'
    )
    parser.add_argument(
        '--password ',
        required=False,
        default=None,
        action='store',
        dest='VCENTER_PASSWORD',
        type=str,
        help='Password for given username on vcenter'
    )
    parser.add_argument(
        '--action ',
        required=False,
        action='store',
        const='ON',
        nargs='?',
        choices=['ON', 'OFF'],
        dest='VCENTER_ACTION',
        type=str,
        default='ON',
        help=('Action that you would like to perform on VMs.'
              ' Options are to turn all machines ON or OFF.')
    )
    args = parser.parse_args()
    cfg = get_config()

    if not args.VCENTER_HOST:
        if cfg.get('vcenter'):
            args.VCENTER_HOST = cfg.get('vcenter').get('hostname')

    if not args.VCENTER_USER:
        if cfg.get('vcenter'):
            args.VCENTER_USER = cfg.get('vcenter').get('username')

    if not args.VCENTER_PASSWORD:
        if cfg.get('vcenter'):
            args.VCENTER_PASSWORD = cfg.get('vcenter').get('password')

    power_control(
        args.VCENTER_HOST,
        args.VCENTER_USER,
        args.VCENTER_PASSWORD,
        args.VCENTER_ACTION)
