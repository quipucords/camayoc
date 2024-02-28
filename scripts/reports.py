#!/usr/bin/env python3
"""
Perform scans and download reports.

This tool is for creating scans and download reports from the sources that
Discovery/Quipucords server supports.
"""
import argparse
import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

from camayoc.data_provider import DataProvider
from camayoc.exceptions import WaitTimeError
from camayoc.qpc_models import Report
from camayoc.qpc_models import ScanJob
from camayoc.tests.qpc.api.v1.utils import wait_until_state

# urllib is a bit too noisy
warnings.filterwarnings("module")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()

TIMEOUT_IN_SECONDS = 240
REPORT_URL = "/api/v1/reports/{id}/"
INSIGHTS_REPORT_URL = REPORT_URL + "insights/"
REPORT_EXTRA_HEADERS = {"Accept": "application/gzip"}
OUTPUT_FILENAME = "{name}_{insights}_{today.year:04}{today.month:02}{today.day:02}.tar.gz"


class SomeScanFailedException(Exception):
    pass


def should_download_insights(data_provider, scan):
    """Decide if insights report should be downloaded.

    Insights makes sense only for network sources.
    """
    source_types = {
        source._id: source.source_type for source in data_provider.sources._created_models.values()
    }
    return any(source_types.get(s, "") == "network" for s in scan.sources)


def run_scan(scan, timeout, include_insights_report):
    """Start a scan and download report files."""
    logger.info("=== Processing scan '%s' ===", scan.name)
    today = datetime.now()
    scanjob = ScanJob(scan_id=scan._id)
    scanjob.create()
    wait_until_state(scanjob, timeout=timeout, state="stopped")
    report = Report()
    report.retrieve_from_scan_job(scan_job_id=scanjob._id)

    report_dest = OUTPUT_FILENAME.format(name=scan.name, insights="", today=today).replace(
        "__", "_"
    )
    logger.info("Saving report to %s", Path(report_dest).resolve().as_posix())
    report_content = scan.client.get(REPORT_URL.format(id=report._id), headers=REPORT_EXTRA_HEADERS)
    with open(report_dest, "bw") as fh:
        fh.write(report_content.content)

    if not include_insights_report:
        return

    insights_report_dest = OUTPUT_FILENAME.format(name=scan.name, insights="insights", today=today)
    logger.info("Saving insights report to %s", Path(insights_report_dest).resolve().as_posix())
    report_content = scan.client.get(
        INSIGHTS_REPORT_URL.format(id=report._id), headers=REPORT_EXTRA_HEADERS
    )
    with open(insights_report_dest, "bw") as fh:
        fh.write(report_content.content)


def run_scans(data_provider, timeout, fail_fast, insights_report):
    """Run all the scans - main program loop."""
    some_scan_failed = False
    for scan in data_provider.scans.defined_many({}):
        download_insights = insights_report and should_download_insights(data_provider, scan)
        try:
            run_scan(scan, timeout, download_insights)
        except WaitTimeError:
            if fail_fast:
                raise SomeScanFailedException
            some_scan_failed = True

    if some_scan_failed:
        raise SomeScanFailedException


def main(args):
    dp = DataProvider()

    retcode = 0
    try:
        run_scans(dp, args.timeout, args.fail_fast, args.insights_report)
    except SomeScanFailedException:
        retcode = 1

    if not args.keep_scans:
        dp.cleanup()

    return retcode


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Perform scans and download reports.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=int(os.environ.get("TIMEOUT", TIMEOUT_IN_SECONDS)),
        help="Timeout in seconds",
    )
    parser.add_argument(
        "-x",
        "--fail-fast",
        action="store_true",
        default=(os.environ.get("FAIL_FAST", "False").capitalize() == "True"),
        help="Exit instantly on first error",
    )
    parser.add_argument(
        "-k",
        "--keep-scans",
        action="store_true",
        default=(os.environ.get("KEEP_SCANS", "False").capitalize() == "True"),
        help="Keep scans, sources and credentials after the execution",
    )
    parser.add_argument(
        "-i",
        "--insights-report",
        action="store_true",
        default=(os.environ.get("INSIGHTS_REPORT", "False").capitalize() == "True"),
        help="Also download insights reports (only for network scans)",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    sys.exit(main(args))
