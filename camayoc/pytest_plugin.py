from collections.abc import Callable

import pytest


def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager) -> None:
    parser.addoption(
        "--camayoc-pipeline",
        dest="camayoc_pipeline",
        choices=("pr", "nightly", "upgrade"),
        help="Only run tests relevant for this pipeline type",
    )


def pytest_collection_modifyitems(
    session: pytest.Session, items: list[pytest.Item], config: pytest.Config
) -> None:
    filter_pipeline_tests(items, config)
    reorder_matching_first(items, _has_fixture("cleaning_data_provider"))
    reorder_matching_first(items, _has_marker("upgrade_only"))


def filter_pipeline_tests(items: list[pytest.Item], config: pytest.Config) -> None:
    """Select tests to run based on --camayoc-pipeline command line argument."""
    pipeline = config.getoption("camayoc_pipeline")
    if not pipeline:
        return

    # gather_*_pipeline_tests return list of items to run, because it feels
    # more natural to say "I want to run these tests" instead of "I want to
    # run everything except these tests".
    # However, later we want to *remove* items from list, so we generate
    # indexes of all items and remove indexes of items we want to keep.
    deselected_items = []
    all_idxs = set(range(len(items)))
    match pipeline:
        case "pr":
            matching_items_idxs = gather_pr_pipeline_tests(items)
        case "nightly":
            matching_items_idxs = gather_nightly_pipeline_tests(items)
        case "upgrade":
            matching_items_idxs = gather_upgrade_pipeline_tests(items)
        case _:
            return
    deselected_idxs = all_idxs - set(matching_items_idxs)

    for node_idx in sorted(deselected_idxs, reverse=True):
        item = items.pop(node_idx)
        deselected_items.append(item)
    config.hook.pytest_deselected(items=deselected_items)


def reorder_matching_first(
    items: list[pytest.Item], predicatefn: Callable[[pytest.Item], bool]
) -> None:
    """Reorder tests so these that match a predicate are run first."""
    matching_node_idxs = []
    for node_idx, node in enumerate(items):
        if predicatefn(node):
            matching_node_idxs.append(node_idx)

    matching_nodes = []
    for node_idx in sorted(matching_node_idxs, reverse=True):
        node = items.pop(node_idx)
        matching_nodes.append(node)

    for node in reversed(matching_nodes):
        items.insert(0, node)


def _has_fixture(fixture_name: str) -> Callable[[pytest.Item], bool]:
    def predicatefn(item: pytest.Item):
        return fixture_name in getattr(item, "fixturenames", [])

    return predicatefn


def _has_marker(marker_name: str) -> Callable[[pytest.Item], bool]:
    def predicatefn(item: pytest.Item):
        marker_names = [i.name for i in item.iter_markers()]
        return marker_name in marker_names

    return predicatefn


def gather_pr_pipeline_tests(items: list[pytest.Item]) -> list[int]:
    """Find items that should be run as part of PR pipeline.

    As of February 2025, that's everything that has NOT been marked
    with nightly_only or upgrade_only markers.
    """
    matching_idxs = []
    for item_idx, item in enumerate(items):
        marker_names = [i.name for i in item.iter_markers()]
        item_is_nightly = "nightly_only" in marker_names
        item_is_upgrade = "upgrade_only" in marker_names
        if not item_is_nightly and not item_is_upgrade:
            matching_idxs.append(item_idx)
    return matching_idxs


def gather_nightly_pipeline_tests(items: list[pytest.Item]) -> list[int]:
    """Find items that should be run as part of nightly pipeline.

    As of February 2025, that's everything that has NOT been marked
    with pr_only or upgrade_only markers.
    """
    matching_idxs = []
    for item_idx, item in enumerate(items):
        marker_names = [i.name for i in item.iter_markers()]
        item_is_pr = "pr_only" in marker_names
        item_is_upgrade = "upgrade_only" in marker_names
        if not item_is_pr and not item_is_upgrade:
            matching_idxs.append(item_idx)
    return matching_idxs


def gather_upgrade_pipeline_tests(items: list[pytest.Item]) -> list[int]:
    """Find items that should be run as part of upgrade pipeline.

    As of February 2025, that's only things that have been marked with
    upgrade_only marker, and end to end tests in UI and CLI.
    """
    matching_idxs = []
    for item_idx, item in enumerate(items):
        marker_names = [i.name for i in item.iter_markers()]
        item_is_upgrade = "upgrade_only" in marker_names
        item_is_endtoend = "test_endtoend.py::test_end_to_end" in item.nodeid
        if item_is_upgrade or item_is_endtoend:
            matching_idxs.append(item_idx)
    return matching_idxs
