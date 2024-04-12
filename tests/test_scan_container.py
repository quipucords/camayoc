from functools import partial
from unittest import mock

from attrs import evolve

from camayoc.data_provider import DataProvider
from camayoc.data_provider import ScanContainer
from camayoc.types.scans import FinishedScan
from camayoc.types.scans import ScanSimplifiedStatusEnum
from camayoc.types.settings import ScanOptions

SCANS = [
    ScanOptions(
        **{
            "name": "networkscan",
            "sources": ["mynetwork"],
            "expected_data": {
                "host1": {
                    "distribution": {
                        "name": "Fedora",
                        "version": "40",
                        "release": "",
                        "is_redhat": False,
                    }
                }
            },
        }
    ),
    ScanOptions(
        **{
            "name": "VCenterOnly",
            "sources": ["vcenter"],
        }
    ),
]


def mocked_run_scans(wanted_scans: set[str], errored_scans: set[str] = set()):
    finished_scans = []
    for scan_name in wanted_scans:
        scan_definition = [scan for scan in SCANS if scan.name == scan_name][0]
        finished_scan = FinishedScan(
            scan_id=1,
            scan_job_id=1,
            definition=scan_definition,
            status=ScanSimplifiedStatusEnum.CREATED,
        )
        if scan_name in errored_scans:
            finished_scan = evolve(
                finished_scan,
                status=ScanSimplifiedStatusEnum.FAILED,
                error=Exception("scan failed"),
            )
        else:
            finished_scan = evolve(
                finished_scan,
                status=ScanSimplifiedStatusEnum.COMPLETED,
                report_id=1,
                details_report={},
                deployments_report={},
            )
        finished_scans.append(finished_scan)
    return finished_scans


def test_run_all():
    """ScanContainer.all() runs and returns all scans at once."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    my_mocked_run_scans = partial(mocked_run_scans, errored_scans=set(["VCenterOnly"]))
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=my_mocked_run_scans
    ) as mock_run_scans:
        scans = sc.all()
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan", "VCenterOnly"},)
        assert len(sc._finished_scans) == len(SCANS)
        assert len(scans) == len(SCANS)


def test_run_ok():
    """ScanContainer.ok() runs all scans, but returns only these without errors."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    my_mocked_run_scans = partial(mocked_run_scans, errored_scans=set(["VCenterOnly"]))
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=my_mocked_run_scans
    ) as mock_run_scans:
        scans = sc.ok()
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan", "VCenterOnly"},)
        assert len(sc._finished_scans) == len(SCANS)
        assert len(scans) == 1


def test_run_name():
    """ScanContainer.with_name() runs only requested scan."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=mocked_run_scans
    ) as mock_run_scans:
        scan = sc.with_name("networkscan")
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan"},)
        assert len(sc._finished_scans) == 1
        assert isinstance(scan, FinishedScan)
        assert scan.definition.name == "networkscan"


def test_expected_attr():
    """ScanContainer.ok_with_expected_data_attr() runs only scans with attr in expected data."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=mocked_run_scans
    ) as mock_run_scans:
        scans = sc.ok_with_expected_data_attr("distribution")
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan"},)
        assert len(sc._finished_scans) == 1
        assert len(scans) == 1


def test_no_attr():
    """ok_with_expected_data_attr does not run any scans when nothing has attr in expected data."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=mocked_run_scans
    ) as mock_run_scans:
        scans = sc.ok_with_expected_data_attr("nonexisting")
        assert mock_run_scans.call_count == 0
        assert len(sc._finished_scans) == 0
        assert len(scans) == 0


def test_dont_run_scans_twice():
    """ScanContainer.all() runs each scan only once."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=mocked_run_scans
    ) as mock_run_scans:
        first_scans = sc.all()
        second_scans = sc.all()
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan", "VCenterOnly"},)
        assert len(sc._finished_scans) == len(SCANS)
        assert len(first_scans) == 2
        assert first_scans == second_scans


def test_run_only_missing_scans():
    """ScanContainer.all() runs only scans that were not run before."""
    dp = DataProvider(credentials=[], sources=[], scans=SCANS)
    sc = ScanContainer(data_provider=dp, scans=SCANS)
    with mock.patch.object(
        sc, "_run_scans", autospec=True, side_effect=mocked_run_scans
    ) as mock_run_scans:
        distro_scans = sc.ok_with_expected_data_attr("distribution")
        assert mock_run_scans.call_count == 1
        assert mock_run_scans.call_args.args == ({"networkscan"},)
        assert len(sc._finished_scans) == 1
        assert len(distro_scans) == 1

        all_scans = sc.all()
        assert mock_run_scans.call_count == 2
        assert mock_run_scans.call_args.args == ({"VCenterOnly"},)
        assert len(sc._finished_scans) == len(SCANS)
        assert len(all_scans) == len(SCANS)
