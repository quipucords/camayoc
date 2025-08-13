#!/usr/bin/env python3

"""Create an OpenShift configuration for Camayoc.

Given an OpenShift instance with credentials and URL to login,
this program will create a Openshift configuration for Camayoc.

Example:
./create-camayoc-ocp-config.py \
   --name shocp4upi415ovn \
   --api-url api.shrocp4upi415ovn.lab \
   --insecure \
   --auth-token sha256~... \
   --output config.local.yaml
"""

import argparse
import json
import subprocess
import sys

import yaml

# Time out limit (in seconds) to log in
TIMEOUT = 60


def has_oc_command():
    cmd = ["command", "-v", "oc"]
    result = subprocess.run(cmd, capture_output=True, check=False, text=True)
    return result.returncode == 0


def login(args):
    url = f"https://{args.api_url}:{args.port}"
    is_insecure_tls = "true" if args.insecure else "false"
    insecure_tls_option = f"--insecure-skip-tls-verify={is_insecure_tls}"
    if args.auth_token:
        cmd = ["oc", "login", url, insecure_tls_option, "--token", args.auth_token]
    else:
        cmd = ["oc", "login", url, insecure_tls_option, "-u", args.username, "-p", args.password]
    try:
        result = subprocess.run(cmd, capture_output=True, check=False, text=True, timeout=TIMEOUT)
    except TypeError:
        print("Error: provide a password or authentication token to login!", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"Error: login timed out after waiting for {TIMEOUT} second(s)", file=sys.stderr)
        return False
    return result.returncode == 0


def get_auth_token():
    cmd = ["oc", "whoami", "-t"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout


def get_cluster_id():
    jsonpath = "{$.items[].spec.clusterID}"
    cmd = ["oc", "get", "clusterversion", "-o", f"jsonpath={jsonpath}"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout


def get_cluster_version():
    cmd = ["oc", "version", "-o", "json"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    version = json.loads(result.stdout)
    return version["openshiftVersion"]


def get_cluster_nodes():
    jsonpath = "{$.items[*].metadata.name}"
    cmd = ["oc", "get", "nodes", "-o", f"jsonpath={jsonpath}"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    nodes = result.stdout.split()
    return nodes


def get_cluster_operators():
    jsonpath = "{$.items[*].metadata.name}"
    cmd = ["oc", "get", "clusteroperators.config.openshift.io", "-o", f"jsonpath={jsonpath}"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    operators = result.stdout.split()
    return operators


def create_ocp_configuration(args, cluster):
    name_and_type = {"name": args.name, "type": "openshift"}
    if args.auth_token:
        auth_method = {"auth_token": args.auth_token}
    else:
        auth_method = {"username": args.username, "password": args.password}
    credential = name_and_type | auth_method
    source = name_and_type | {
        "hosts": [args.api_url],
        "credentials": [args.name],
        "ssl_cert_verify": not args.insecure,
    }
    scan = {
        "name": args.name,
        "sources": [args.name],
        "expected_data": {args.name: {"cluster_info": cluster}},
    }
    config = {"credentials": [credential], "sources": [source], "scans": [scan]}
    return yaml.dump(config, sort_keys=False)


def create_configuration(args, cluster):
    yaml_dynaconf_merge = f"dynaconf_merge: {'true' if args.dynaconf_merge else 'false'}"
    ocp_output = create_ocp_configuration(args, cluster)
    output = f"{yaml_dynaconf_merge}\n{ocp_output}"
    with args.output as fd:
        fd.write(output)


def get_cluster_information():
    cluster = {
        "cluster_id": get_cluster_id(),
        "version": get_cluster_version(),
        "nodes": get_cluster_nodes(),
        "operators": get_cluster_operators(),
    }
    return cluster


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create an OpenShift configuration for Camayoc.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        default="ocp",
        help="The common name for credentials, sources and scans.",
    )
    parser.add_argument(
        "-a", "--api-url", required=True, default="localhost", help="Provide the API URL to log in."
    )
    parser.add_argument("-P", "--port", type=int, default=6443, help="Provide the API port number.")
    parser.add_argument(
        "-k", "--insecure", action="store_true", help="Skip the SSL verification step."
    )
    parser.add_argument(
        "-u", "--username", default="kubeadmin", help="Provide the username to log in."
    )
    parser.add_argument("-p", "--password", help="Provide the password to log in.")
    parser.add_argument("-t", "--auth-token", help="Provide the token to log in.")
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w", encoding="UTF-8"),
        default=sys.stdout,
        help="Write to file instead of stdout.",
    )
    parser.add_argument(
        "-m",
        "--dynaconf-merge",
        action="store_true",
        help="Merge configurations, otherwise overwrite. See also https://www.dynaconf.com/merging/",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a trial run without connecting."
    )
    args = parser.parse_args()
    return args


def main():
    cluster_info = {}
    args = parse_args()
    if not args.dry_run:
        if not has_oc_command():
            print("Could not find the 'oc' command", file=sys.stderr)
            return 1
        if not login(args):
            print(f"Could not log in to '{args.api_url}:{args.port}'", file=sys.stderr)
            return 1
        cluster_info = get_cluster_information()
    create_configuration(args, cluster_info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
