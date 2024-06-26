# coding=utf-8
"""Pytest customizations and fixtures for the quipucords tests."""

import pytest

from camayoc import utils
from camayoc.config import settings


def pytest_collection_modifyitems(
    session: pytest.Session, items: list[pytest.Item], config: pytest.Config
) -> None:
    cleaning_dp_node_idxs = []
    for node_idx, node in enumerate(items):
        if "cleaning_data_provider" in node.fixturenames:
            cleaning_dp_node_idxs.append(node_idx)

    cleaning_dp_nodes = []
    for node_idx in sorted(cleaning_dp_node_idxs, reverse=True):
        node = items.pop(node_idx)
        cleaning_dp_nodes.append(node)

    for node in reversed(cleaning_dp_nodes):
        items.insert(0, node)


@pytest.fixture
def isolated_filesystem(request):
    """Fixture that creates a temporary directory.

    Changes the current working directory to the created temporary directory
    for isolated filesystem tests.
    """
    # Create isolated filesystem directory in the ssh_keyfile_path
    # configuration location if marked with `ssh_keyfile_path`.
    mark = request.node.get_closest_marker("ssh_keyfile_path")
    ssh_keyfile_path = None
    if mark:
        ssh_keyfile_path = settings.quipucords_server.ssh_keyfile_path
        if not ssh_keyfile_path:
            pytest.fail("QPC configuration 'ssh_keyfile_path' not provided or found")
    with utils.isolated_filesystem(ssh_keyfile_path) as path:
        yield path
