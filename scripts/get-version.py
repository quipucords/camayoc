"""
Obtain versions of Quipucords & co installed in environment.

This script is used by CI to set test run metadata.
"""
import argparse
import json
import subprocess
from operator import itemgetter

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
        return qpc_build_result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Jenkins uses CLI image downloaded from quay
    podman_images_cmd = ["podman", "images", "--format", "json"]
    podman_images_result = subprocess.run(
        podman_images_cmd, capture_output=True, check=True, text=True
    )
    podman_images = json.loads(podman_images_result.stdout.strip())
    podman_images = [
        image for image in podman_images if "quipucords.cli.git_sha" in image.get("Labels")
    ]
    podman_images = sorted(podman_images, key=itemgetter("Created"), reverse=True)
    if podman_images:
        return podman_images[0]["Labels"]["quipucords.cli.git_sha"]

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
