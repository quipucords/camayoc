import os
from pathlib import Path
from pprint import pformat

import pytest
from deepdiff.diff import DeepDiff

from camayoc.config import settings
from camayoc.db_snapshot import DBSnapshot


def compare_snapshots_handler(differences: DeepDiff):
    node_name = os.getenv("NODE_NAME", "local")
    results_dir = Path(".").cwd() / "test-results" / f"compare-snapshots-{node_name}"
    results_dir.mkdir(parents=True, exist_ok=True)
    for key, value in differences.items():
        filepath = results_dir / f"{key}.txt"
        filepath.write_text(pformat(value))
    return f"Details of differences are saved in {results_dir.as_posix()}/"


@pytest.mark.upgrade_only
@pytest.mark.skipif(
    not all(
        (settings.camayoc.snapshot_test_reference_path, settings.camayoc.snapshot_test_actual_path)
    ),
    reason=(
        "Both camayoc.snapshot_test_reference_path and "
        "camayoc.snapshot_test_actual_path must be set"
    ),
)
def test_compare_snapshots():
    """Verify that user-facing data survives the upgrade.

    :id: f85334a1-85db-4338-ba41-982fed14d978
    :description: Verify that user-facing data survives the upgrade.
    :steps:
        1) Read reference snapshot data (created before upgrade)
        2) Read actual snapshot data (created after upgrade)
        3) Compare them
    :expectedresults: Post-upgrade data matches pre-upgrade data.
    """
    reference = DBSnapshot.from_dir(settings.camayoc.snapshot_test_reference_path)
    actual = DBSnapshot.from_dir(settings.camayoc.snapshot_test_actual_path)

    differences = DeepDiff(reference, actual)

    assert not differences, compare_snapshots_handler(differences)
