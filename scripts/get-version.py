"""
Obtain versions of Quipucords & co installed in environment.

This script is used by CI to set test run metadata.
"""

import argparse
import subprocess

from camayoc import api
from camayoc.utils import client_cmd


def get_backend_version():
    api_client = api.Client()
    server_status = api_client.get("status/")
    server_version = server_status.json().get("server_version")
    return server_version


def get_frontend_version():
    raise NotImplementedError("Obtaining frontend version is not supported yet")


def get_cli_version():
    # Use --build-sha flag if available
    qpc_build_cmd = [client_cmd, "--build-sha"]
    try:
        qpc_build_result = subprocess.run(qpc_build_cmd, capture_output=True, check=True, text=True)
        qpc_build_result = qpc_build_result.stdout.strip()
        if qpc_build_result.lower() != "unknown":
            return qpc_build_result
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Jenkins will use CLI installed from rpm package
    try:
        cmd = [
            "rpm",
            "-qa",
            "--queryformat",
            "%{NAME}:version=%{VERSION} provideversion=%{PROVIDEVERSION}\n",
        ]
        rpm_qa_result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        for pkg_line in rpm_qa_result.stdout.split("\n"):
            if not pkg_line:
                continue
            pkg_name, pkg_version = pkg_line.split(":", maxsplit=1)
            if pkg_name in ("qpc", "discovery-cli"):
                return pkg_version
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Failover value for local runs, where qpc may be installed from git
    cmd = ["git", "-C", "../qpc/", "rev-parse", "HEAD"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout.strip()


def get_camayoc_version():
    cmd = ["git", "rev-parse", "HEAD"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        prog="get-versions", description="Get versions of Quipucords & co in this environment"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backend", action="store_true")
    group.add_argument("--frontend", action="store_true")
    group.add_argument("--cli", action="store_true")
    group.add_argument("--camayoc", action="store_true")

    args = parser.parse_args()
    if args.backend:
        version_number = get_backend_version()
    elif args.frontend:
        version_number = get_frontend_version()
    elif args.cli:
        version_number = get_cli_version()
    elif args.camayoc:
        version_number = get_camayoc_version()

    print(version_number)


if __name__ == "__main__":
    main()
