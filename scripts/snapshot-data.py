#!/usr/bin/env python3
"""
Save a snapshot of server data in directory.

This is part of database migrations testing pipeline. Usually you create an instance
and take a snapshot of data. Then you stand up new instance, load database from backup
and take another snapshot. Then you can compare snapshots and draw conclusions.
"""

import argparse
import logging
import warnings
from pathlib import Path

from camayoc.db_serializer import DBSerializer

# urllib is a bit too noisy
warnings.filterwarnings("module")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Save a snapshot of server data in directory, usually for future comparisons.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing files",
    )
    parser.add_argument(
        "destination",
        type=Path,
        help="Path to directory where data will be stored. Will be created if does not exist.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    serializer = DBSerializer(args.destination, args.force)
    serializer.serialize()
