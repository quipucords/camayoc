# coding=utf-8
"""Update scan facts in config file given scan data.

Run this script as a command line tool generate a camayoc config file.
gen_config.py uses data from a csv file with profile infomration and a csv file
from rho scan.

Refer to gen_hosts() docstring for information about what data needs to be
present in the profile csv file.


.. note::

    This tool reads in your camayoc config file in $XDG_CONFIG_HOME and outputs
    it to the $CWD with new data. It discards old hosts and profile data but
    uses auth data and other data provided in your $XDG_CONFIG_HOME config file
    (if it exists). This does not modify your $XDG_CONFIG_HOME config file
    directly, that is left to you. Always backup your old config file before
    you replace it with the generated one!

Example:
    .. code-block:: bash

        python gen_config.py --profiles profiles.csv --report report.csv
"""

import argparse
import csv
import os
import uuid

import yaml

from camayoc import config
from camayoc.exceptions import ConfigFileNotFoundError


BASE_CONFIG = """
rho:
  auths:
    - username: root
      name: default
      sshkeyfile: $HOME/.ssh/id_rsa
"""


def get_config():
    """Gather existing config file or create one.

    If a config file is found by camayoc, use that.
    Otherwise, use BASE_CONFIG as auth.
    """
    try:
        cfg = config.get_config()
    except ConfigFileNotFoundError:
        cfg = yaml.load(BASE_CONFIG, Loader=yaml.FullLoader)

    return cfg, os.path.join(os.getcwd(), "config.yaml")


def gen_hosts(profilepath, reportpath):
    """Generate list of hosts from profile and report data.

    :param profilepath: Path to profile csv file).
        This should be a csv file with the columns:

        * name
        * ip
        * profile
        * auth
    :param reportpath: Path to report csv file.  Expects csv from rho scan.
        The keys and values will be used as facts to test agains.  The
        date.date fact if present is automatically excluded.

        If you would like other facts excluded, delete the columns containing
        those facts.

        .. note::
            It will generated all new hosts, old host data is discarded.
    """
    hosts = []
    with open(profilepath) as csvfile:
        hostdata = csv.DictReader(csvfile)
        for row in hostdata:
            hosts.append(
                {
                    "hostname": row.get("name", ""),
                    "ip": row.get("ip", ""),
                    "provider": "vcenter" if "vc" in row.get("name", "") else "",
                    "facts": {},
                    "profile": row.get("profile", uuid.uuid4()),
                    "auth": row.get("auth", ""),
                    "privileged": row.get("privileged"),
                }
            )
    with open(reportpath) as csvfile:
        scan_results = csv.DictReader(csvfile)
        for row in scan_results:
            for host in hosts:
                if host["ip"] == row.get("connection.host"):
                    for k, v in row.items():
                        if "date" not in k:
                            if k in ["cpu.bogomips", "dmi.bios-version"] and is_float(
                                v
                            ):
                                host["facts"][k] = "%.2f" % float(v)
                            else:
                                host["facts"][k] = v

    return hosts


def is_float(s):
    """Test to see if the string can be converted to float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def gen_profiles(cfg, hosts):
    """Generate profiles for a given config and hosts.

    :param cfg: A valid camayoc config object

    :param hosts: A list of valid hosts
        Can be provided by the output of gen_hosts(profilepath, reportpath)

    :rtype profiles: A list of valid profiles for camayoc config

    If hosts have profiles associated with them, they will be added to
    appropriate profile.

    If the profile exists, they will be added to it. If it does not,
    a new profile is generated.

    If the profile does not contain the auth matching the host, the
    auth will be added.

    .. note::
        This is "constructive", as in it adds profiles and modifies profiles,
        but does not delete existing profiles.
    """
    profiles = cfg.get("profiles", [])
    for host in hosts:
        # first append hosts to any existing profiles
        profile_found = False
        for profile in profiles:
            if host.get("profile", "") == profile.get("name", uuid.uuid4()):
                profile_found = True
                if host.get("ip", "") not in profile.get("hosts", []):
                    if host["ip"] != "":
                        profile["hosts"].append(host["ip"])
                if host["auth"] not in profile.get("auths", []):
                    if host["auth"] != "":
                        profile["auths"].append(host["auth"])
        if not profile_found:
            profiles.append(
                {
                    "name": host["profile"],
                    "hosts": [host["ip"]],
                    "auths": [host["auth"]],
                    "privileged": host.get("privileged"),
                }
            )

    return profiles


def write_config(cfg, hosts, profiles, configfile):
    """Write changes to camayoc config file.

    :param cfg: A valid camayoc config
    :param hosts: A list of valid hosts
        Can be provided by the output of gen_hosts()

    :param profiles: A list of valid profiles for camayoc config
        Can be provided by the output of gen_profiles()
    :param configfile:
        The path to the config file where we will write the new config.

    Given an existing config, hosts, profiles, and the path to the new config
    file, form the new config and write it to the file.
    """
    cfg["rho"]["hosts"] = hosts
    cfg["rho"]["profiles"] = profiles
    with open(configfile, "w") as outfile:
        yaml.dump(cfg, outfile, default_style="'", default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate facts to test in config file from scan file."
    )
    parser.add_argument(
        "--profiles ",
        required=True,
        action="store",
        dest="profilecsv",
        type=str,
        default="profiles.csv",
        help="absolute path to csv containing profile to ip to auth mapping",
    )
    parser.add_argument(
        "--report ",
        required=True,
        action="store",
        dest="reportcsv",
        type=str,
        default="report.csv",
        help="absolute path to csv containing rho scan with facts to test",
    )
    args = parser.parse_args()
    for arg in [args.profilecsv, args.reportcsv]:
        if not os.path.isfile(arg):
            raise IOError(
                "{} not found. Provide absolute path to existing file.".format(arg)
            )
    cfg, configfile = get_config()
    hosts = gen_hosts(args.profilecsv, args.reportcsv)
    profiles = gen_profiles(cfg, hosts)
    write_config(cfg, hosts, profiles, configfile)
