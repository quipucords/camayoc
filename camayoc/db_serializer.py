import io
import json
import logging
import re
import tarfile
from pathlib import Path

from camayoc import api
from camayoc.constants import DBSERIALIZER_CONNECTIONJOBS_DIR_PATH
from camayoc.constants import DBSERIALIZER_CREDENTIALS_FILE_PATH
from camayoc.constants import DBSERIALIZER_REPORTS_DIR_PATH
from camayoc.constants import DBSERIALIZER_SCANJOBS_DIR_PATH
from camayoc.constants import DBSERIALIZER_SCANS_FILE_PATH
from camayoc.constants import DBSERIALIZER_SOURCES_FILE_PATH
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Report
from camayoc.qpc_models import Scan
from camayoc.qpc_models import ScanJob
from camayoc.qpc_models import Source

logger = logging.getLogger(__name__)


class DBSerializer:
    def __init__(self, destination: Path, overwrite=False):
        self._destination = destination
        self._overwrite = overwrite
        self._client: api.Client | None = None

    def serialize(self):
        self._destination.mkdir(parents=True, exist_ok=True)
        self._client = api.Client()

        self._serialize_credentials()
        self._serialize_sources()
        self._serialize_scans()
        self._serialize_jobconnectionresults()
        self._serialize_scanjobs()
        self._serialize_reports()

    def _serialize_credentials(self):
        destination = self._destination / DBSERIALIZER_CREDENTIALS_FILE_PATH
        if not self.__check_destination(destination):
            return

        cred = Credential(client=self._client)
        all_credentials = self.__list_paged(cred.list)
        self.__save_json(all_credentials, destination)

    def _serialize_sources(self):
        destination = self._destination / DBSERIALIZER_SOURCES_FILE_PATH
        if not self.__check_destination(destination):
            return

        source = Source(client=self._client)
        all_sources = self.__list_paged(source.list)
        self.__save_json(all_sources, destination)

    def _serialize_scans(self):
        destination = self._destination / DBSERIALIZER_SCANS_FILE_PATH
        if not self.__check_destination(destination):
            return

        scan = Scan(client=self._client)
        all_scans = self.__list_paged(scan.list)
        self.__save_json(all_scans, destination)

    def _serialize_jobconnectionresults(self):
        def gen_job_ids(all_sources):
            for source_json in all_sources:
                if job_id := source_json.get("connection", {}).get("id"):
                    yield job_id

        sources_file = self._destination / DBSERIALIZER_SOURCES_FILE_PATH
        with sources_file.open() as fh:
            all_sources = json.load(fh)

        for job_id in gen_job_ids(all_sources):
            sources_destination = self._destination / DBSERIALIZER_CONNECTIONJOBS_DIR_PATH
            sources_destination.mkdir(parents=True, exist_ok=True)

            destination = sources_destination / f"connection_{job_id}.json"
            if not self.__check_destination(destination):
                continue

            scanjob = ScanJob(client=self._client, _id=job_id)
            all_connectionjobs = self.__list_paged(scanjob.connection_results)
            self.__save_json(all_connectionjobs, destination)

    def _serialize_scanjobs(self):
        scans_file = self._destination / DBSERIALIZER_SCANS_FILE_PATH
        with scans_file.open() as fh:
            all_scans = json.load(fh)

        scan_ids = [scan_json.get("id") for scan_json in all_scans]

        for scan_id in scan_ids:
            scans_destination = self._destination / DBSERIALIZER_SCANJOBS_DIR_PATH
            scans_destination.mkdir(parents=True, exist_ok=True)

            destination = scans_destination / f"jobs_{scan_id}.json"
            if not self.__check_destination(destination):
                continue

            scanjob = ScanJob(client=self._client, scan_id=scan_id)
            all_scanjobs = self.__list_paged(scanjob.list)
            self.__save_json(all_scanjobs, destination)

    def _serialize_reports(self):  # noqa: C901
        def gen_report_ids(all_scans):
            for scan_json in all_scans:
                for job in scan_json.get("jobs", []):
                    if report_id := job.get("report_id"):
                        yield report_id

        def extractfiles(tar, destination, filename_patterns):
            for member in tar.getmembers():
                member_name = Path(member.name).name
                if not any(re.fullmatch(regex, member_name) for regex in filename_patterns):
                    continue
                file_destination = destination / member_name
                if not self.__check_destination(file_destination):
                    continue
                if tar_fh := tar.extractfile(member):
                    file_destination.write_bytes(tar_fh.read())

        scans_file = self._destination / DBSERIALIZER_SCANS_FILE_PATH
        with scans_file.open() as fh:
            all_scans = json.load(fh)

        for report_id in gen_report_ids(all_scans):
            report_destination = self._destination / DBSERIALIZER_REPORTS_DIR_PATH / str(report_id)
            report_destination.mkdir(parents=True, exist_ok=True)

            report = Report(client=self._client, _id=report_id)
            gzip_response = report.reports_gzip()
            gzip_response.raise_for_status()

            tar_bytes = io.BytesIO(gzip_response.content)
            with tarfile.open(fileobj=tar_bytes, mode="r:gz") as tar:
                extractfiles(tar, report_destination, (r"details.*\.json", r"aggregate.*\.json"))

    def __list_paged(self, obj_fn):
        all_objs = []
        page = 1
        while True:
            payload = {"page": page}
            http_response = obj_fn(params=payload)
            http_response.raise_for_status()
            response_json = http_response.json()

            if results := response_json.get("results"):
                all_objs.extend(results)

            if not response_json.get("next"):
                break

            page += 1

        return all_objs

    def __check_destination(self, destination: Path) -> bool:
        may_write = not destination.exists() or self._overwrite
        if not may_write:
            logger.info(
                "Refusing to overwrite file that already exists [destination=%s]",
                destination.as_posix(),
            )
        return may_write

    def __save_json(self, json_data, destination: Path) -> None:
        with destination.open("w") as fh:
            json.dump(json_data, fh)
