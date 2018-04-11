# coding=utf-8
"""Utility functions."""

import time

from camayoc import cli


def is_live(client, server, num_pings=10):
    """Test if server responds to ping.

    Returns true if server is reachable, false otherwise.
    """
    client.response_handler = cli.echo_handler
    ping = client.run(('ping', '-c', num_pings, server))
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

    `See rho issue #302 <https://github.com/quipucords/rho/issues/302>`_
    """
    system = cli.System(hostname='localhost', transport='local')
    client = cli.Client(system)

    unreached = servers
    while unreached and timeout > 0:
        unreached = [host for host in unreached if not is_live(client, host)]
        time.sleep(10)
        timeout -= 10
