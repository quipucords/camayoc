# coding=utf-8
"""Pytest customizations and fixtures for tests to execute on remote hosts."""
import os
import pytest
from camayoc import cli, config
from camayoc.exceptions import ConfigFileNotFoundError
from time import sleep
from camayoc.constants import (
    VCENTER_DATA_CENTER,
    VCENTER_CLUSTER,
    VCENTER_HOST,
)


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
        sleep(10)
        timeout -= 10


@pytest.fixture(scope='session', autouse=True)
def manage_systems(request):
    """Fixture that manages remote systems.

    At the beginning of a session, hosts will be turned on. We must wait for
    the machines to complete booting so there is about 30 seconds of overhead
    at the beginning before test begin executing.

    At the end of the session, they are turned off.

    Hosts must have a "provider" specified in the config file, otherwise they
    will be skipped and assumed to be accessible by rho.

    Hosts that are powered on at the beginning of the session are then powered
    down at the end of the session.

    Example::

        #/home/user/.config/camayoc/config.yaml
        rho:
          auths:
            - username: root
              name: sonar
              sshkeyfile: /home/elijah/.ssh/id_sonar_jenkins_rsa
          hosts:
            - hostname: string-name-of-vm-on-vcenter
              ip: XX.XX.XXX.XX
              provider: vcenter
              facts:
                connection.port: 22
                cpu.count: 1
          profiles:
            - name: profile1
              auths:
                - auth1
              hosts:
                - XX.XX.XXX.XX
         vcenter:
          hostname: **Required** -- url to vcenter instance
          username: **optional** -- will first try environment variable $VCUSER
          password: **optional** -- will first try environment variable $VCPASS

    .. warning::

        It is a bad idea to have multiple sessions of pytest running
        concurrently against the same hosts/config file.
        If one session ends before another, it will power down the
        machines leaving the other one to fail.
    """
    from pyVim.connect import SmartConnect, Disconnect
    import ssl

    try:
        cfg = config.get_config()
    except ConfigFileNotFoundError:
        # if we don't have a config file, do nothing
        return

    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode = ssl.CERT_NONE
    # try and make a secure connection first
    if 'vcenter' in cfg.keys():
        if os.getenv('VCUSER', False):
            vcuser = os.environ['VCUSER']
        else:
            vcuser = cfg['vcenter']['username']
        if os.getenv('VCPASS', False):
            vcpassword = os.environ['VCPASS']
        else:
            vcpassword = cfg['vcenter']['password']
        try:
            c = SmartConnect(
                host=cfg['vcenter']['hostname'],
                user=vcuser,
                pwd=vcpassword
            )
        except ssl.SSLError:
            c = SmartConnect(
                host=cfg['vcenter']['hostname'],
                user=vcuser,
                pwd=vcpassword,
                sslContext=s
            )
        # these index choices are particular to our VCenter setup
        fldr = c.content.rootFolder.childEntity[VCENTER_DATA_CENTER].hostFolder
        vm_host = fldr.childEntity[VCENTER_CLUSTER].host[VCENTER_HOST]
        # the host has a property "vm" which is a list of VMs
        vms = vm_host.vm
        vc_hosts = []
        for host in cfg['rho']['hosts']:
            if ('provider' in host.keys()) and (
                    host['provider'] == 'vcenter'):
                vc_hosts.append(host['ip'])
                for vm in vms:
                    if vm.name == host['hostname']:
                        if vm.runtime.powerState == 'poweredOff':
                            vm.PowerOnVM_Task()
        # need to wait for machines to boot and start sshd
        wait_until_live(vc_hosts)

    def shutdown_systems():
        """Turn off hosts at the end of a session.

        This runs once at the end of each session.
        """
        try:
            cfg = config.get_config()
        except ConfigFileNotFoundError:
            # if we don't have a config file, do nothing
            return

        for host in cfg['rho']['hosts']:
            if ('provider' in host.keys()) and (host['provider'] == 'vcenter'):
                for vm in vms:
                    if vm.name == host['hostname']:
                        if vm.runtime.powerState == 'poweredOn':
                            vm.PowerOffVM_Task()
        Disconnect(c)

    #  this line makes this part of the fixture only run at end of session
    #  pytest provides us this request object
    request.addfinalizer(shutdown_systems)  # noqa: F821
