# coding=utf-8
"""Utility functions."""

import contextlib
import time

from pyVmomi import vim

from camayoc import cli


def get_vcenter_vms(vcenter_client):
    """Return a list of available vCenter vms.

    :param vcenter_client: A connected vCenter client which will be used to
        retrieve the list of all available vms.
    """
    view = vcenter_client.content.viewManager.CreateContainerView(
        vcenter_client.content.rootFolder, [vim.VirtualMachine], True
    )
    return view.view


def is_vm_powered_on(vm):
    """Check if a vCenter vm is powered on.

    A vm is considered powered on when the VMWare Tools are installed, its
    power state is powered on and its IP address can be fetched.
    """
    # Be noisy if VMWare Tools is not installed.
    assert vm.guest.toolsStatus != "toolsNotInstalled"

    return all(
        [
            vm.runtime.powerState == "poweredOn",
            vm.guestHeartbeatStatus == "green",
            vm.guest.ipAddress is not None,
        ]
    )


def power_on_vms(vms, timeout=300):
    """Power on the vCenter vms.

    For each virtual machine: ensure that the VMWare Tools are installed, they
    are powered on and its IP address can be fetched.
    """
    vms_to_wait = []
    for vm in vms:
        if not is_vm_powered_on(vm):
            vm.PowerOnVM_Task()
            vms_to_wait.append(vm)

    while vms_to_wait and timeout > 0:
        vms_to_wait = [vm for vm in vms_to_wait if not is_vm_powered_on(vm)]
        time.sleep(10)
        timeout -= 10

    if vms_to_wait:
        assert timeout <= 0, (
            f"Could not power on all {vms}, timed out waiting for " f"{vms_to_wait}"
        )


def power_off_vms(vms, timeout=300):
    """Gracefully shutdown the vCenter vms."""
    vms_to_wait = []
    for vm in vms:
        if vm.runtime.powerState != "poweredOff":
            vm.ShutdownGuest()
            vms_to_wait.append(vm)

    while vms_to_wait and timeout > 0:
        vms_to_wait = [
            vm for vm in vms_to_wait if vm.runtime.powerState != "poweredOff"
        ]
        time.sleep(10)
        timeout -= 10

    if vms_to_wait:
        assert timeout <= 0, (
            f"Could not power off all {vms}, timed out waiting for " f"{vms_to_wait}"
        )


@contextlib.contextmanager
def vcenter_vms(vms):
    """Ensure vCenter machines are on and will be properly off.

    Given a list of vCenter VM managed objects ensure all of them are on then
    yeild the vms list. Ensure they will be turned off before closing the
    context.
    """
    power_on_vms(vms)
    try:
        yield vms
    finally:
        power_off_vms(vms)


def is_live(client, server, num_pings=10):
    """Test if server responds to ping.

    Returns true if server is reachable, false otherwise.
    """
    client.response_handler = cli.echo_handler
    ping = client.run(("ping", "-c", num_pings, server))
    return ping.returncode == 0


def wait_until_live(servers, timeout=360):
    """Wait for servers to be live.

    For each server in the "servers" list, verify if it is reachable.
    Keep trying until a connection is made for all servers or the timeout
    limit is reached.

    If the timeout limit is reached, we exit even if there are unreached hosts.
    This means tests could fail with "No auths valid for this profile" if every
    host in the profile is unreachable. Otherwise, if there is at least one
    valid host, the scan will go on and only facts about reached hosts will be
    tested.
    """
    system = cli.System(hostname="localhost", transport="local")
    client = cli.Client(system)

    unreached = servers
    while unreached and timeout > 0:
        unreached = [host for host in unreached if not is_live(client, host)]
        time.sleep(10)
        timeout -= 10
