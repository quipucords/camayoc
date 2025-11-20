"""
Obtain versions of Quipucords & co installed in environment.

This script is used by CI to set test run metadata.
"""

import argparse
import json
import subprocess

from camayoc import api
from camayoc.utils import client_cmd


def rpm_pkg_versions(*package_names):
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
            if pkg_name in package_names:
                return pkg_version
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_backend_version():
    api_client = api.Client()
    server_status = api_client.get("v1/status/")
    server_version = server_status.json().get("server_version")
    return server_version


def get_frontend_version():
    podman_ps_a_cmd = ["podman", "ps", "-a", "--format=json"]
    podman_ps_a_result = subprocess.run(
        podman_ps_a_cmd, capture_output=True, text=True, check=False
    )
    if podman_ps_a_result.returncode != 0:
        return

    app_cids = [f"{app_name}-app.cid" for app_name in ("quipucords", "discovery")]
    app_names = {f"{app_name}-app" for app_name in ("quipucords", "discovery")}
    containers = json.loads(podman_ps_a_result.stdout)
    for container in containers:
        cid = container.get("CIDFile", "")
        names = container.get("Names", [])
        if not cid.endswith(tuple(app_cids)) and set(names).isdisjoint(app_names):
            continue
        image_id = container.get("ImageID")
        versions = [f"image_id={image_id}"]
        if git_sha := container.get("Labels", {}).get("quipucords.frontend.git_sha"):
            versions.append(f"git_sha={git_sha}")
        return " ".join(versions)


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
    if found_rpms := rpm_pkg_versions("qpc", "discovery-cli"):
        return found_rpms

    # Failover value for local runs, where qpc may be installed from git
    cmd = ["git", "-C", "../qpc/", "rev-parse", "HEAD"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout.strip()


def get_installer_version():
    # Jenkins will use CLI installed from rpm package
    if found_rpms := rpm_pkg_versions("quipucords-installer", "discovery-installer"):
        return found_rpms

    # Failover value for local runs, where qpc may be installed from git
    cmd = ["git", "-C", "../quipucords-installer/", "rev-parse", "HEAD"]
    result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    return result.stdout.strip()


def get_ctl_version():
    # Jenkins will use CLI installed from rpm package
    if found_rpms := rpm_pkg_versions("quipucordsctl", "discoveryctl"):
        return found_rpms

    # Failover value for local runs, where qpc may be installed from git
    cmd = ["git", "-C", "../quipucordsctl/", "rev-parse", "HEAD"]
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
    group.add_argument("--installer", action="store_true")
    group.add_argument("--ctl", action="store_true")

    args = parser.parse_args()
    if args.backend:
        version_number = get_backend_version()
    elif args.frontend:
        version_number = get_frontend_version()
    elif args.cli:
        version_number = get_cli_version()
    elif args.camayoc:
        version_number = get_camayoc_version()
    elif args.installer:
        version_number = get_installer_version()
    elif args.ctl:
        version_number = get_ctl_version()

    print(version_number)


if __name__ == "__main__":
    main()
