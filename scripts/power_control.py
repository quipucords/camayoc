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
import re
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


def power_control(vcenter_host,
                  vcenter_user,
                  vcenter_password,
                  vcenter_action,
                  pattern):
    """Connect to vcenter and perform action on all sonar machines."""
    try:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_password,
        )
    except ssl.SSLError:
        c = SmartConnect(
            host=vcenter_host,
            user=vcenter_user,
            pwd=vcenter_password,
            sslContext=ssl._create_unverified_context(),
        )

    dc = c.content.rootFolder.childEntity[VCENTER_DATA_CENTER]
    vms = dc.hostFolder.childEntity[VCENTER_CLUSTER].host[VCENTER_HOST_INDX].vm

    pattern_matcher = re.compile(pattern)
    for vm in vms:
        if pattern_matcher.findall(vm.name):
            if vcenter_action == 'ON':
                if vm.runtime.powerState == 'poweredOff':
                    vm.PowerOnVM_Task()
            if vcenter_action == 'OFF':
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
        dest='vcenter_host',
        type=str,
        help=('This is the hostname where you would log into vcenter from a'
              ' browser')
    )
    parser.add_argument(
        '--user ',
        required=False,
        default=None,
        action='store',
        dest='vcenter_user',
        type=str,
        help='Username on vcenter'
    )
    parser.add_argument(
        '--password ',
        required=False,
        default=None,
        action='store',
        dest='vcenter_password',
        type=str,
        help='Password for given username on vcenter'
    )
    parser.add_argument(
        '--pattern ',
        required=False,
        default='^sonar-',
        action='store',
        dest='pattern',
        type=str,
        help='String to match for VM names. Accepts regular expressions.'
    )
    parser.add_argument(
        '--action ',
        required=False,
        action='store',
        const='ON',
        nargs='?',
        choices=['ON', 'OFF'],
        dest='vcenter_action',
        type=str,
        default='ON',
        help=('Action that you would like to perform on VMs.'
              ' Options are to turn all machines ON or OFF.')
    )
    args = parser.parse_args()
    cfg = get_config()

    if not args.vcenter_host:
        if cfg.get('vcenter'):
            args.vcenter_host = cfg.get('vcenter').get('hostname')

    if not args.vcenter_user:
        if cfg.get('vcenter'):
            args.vcenter_user = cfg.get('vcenter').get('username')

    if not args.vcenter_password:
        if cfg.get('vcenter'):
            args.vcenter_password = cfg.get('vcenter').get('password')

    power_control(
        args.vcenter_host,
        args.vcenter_user,
        args.vcenter_password,
        args.vcenter_action,
        args.pattern,
    )
