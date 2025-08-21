from __future__ import annotations

import time
from datetime import datetime
from functools import wraps

from playwright.sync_api import Download
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from camayoc.exceptions import FailedScanException
from camayoc.types.ui import SummaryReportData
from camayoc.types.ui import SummaryReportDataPoint
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import ColumnOrdering
from camayoc.ui.enums import Pages
from camayoc.ui.enums import ScansModalTableColumns

from ..components.items_list import AbstractListItem
from ..components.modal import Modal
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage

REFRESH_BUTTON_LOCATOR = "div[class*=-c-toolbar] button[data-ouia-component-id=refresh]"


class ScanHistoryModal(Modal, AbstractPage):
    SAVE_LOCATOR = None
    CANCEL_LOCATOR = "*[class$='modal-box__close'] button"
    SAVE_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = Pages.SCANS

    def sort_table(self, sort_by: ScansModalTableColumns, ordering: ColumnOrdering) -> None:
        tries = 0
        table_header_locator = (
            "table[data-ouia-component-id=scan_jobs_table] thead "
            f"th[data-ouia-component-id={sort_by.value}]"
        )
        while 3 >= tries:
            header = self._driver.locator(table_header_locator)
            if header.get_attribute("aria-sort") == ordering.value:
                return
            header.locator("button").click()
            tries += 1
        raise RuntimeError("Failed to sort table")

    def get_nth_download(self, item: int) -> Download:
        table_row_locator = "table[data-ouia-component-id=scan_jobs_table] tbody tr"
        download_button_locator = "td[data-label=Download] button"

        last_download = self._driver.locator(table_row_locator).nth(item)
        with self._driver.expect_download() as download_info:
            last_download.locator(download_button_locator).click(timeout=10_000)
        download = download_info.value
        download.path()  # blocks the script while file is downloaded
        return download


def to_int(value: str):
    try:
        return int(value)
    except ValueError:
        return None


def to_date(value: str):
    try:
        dt = datetime.strptime(value.strip(), "%d %B %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


class SummaryReportModal(Modal, AbstractPage):
    CANCEL_LOCATOR = "*[class$='modal-box__close'] button"
    CANCEL_RESULT_CLASS = Pages.SCANS
    VALUE_TRANSFORMER_MAP = {
        "system_creation_date_average": to_date,
    }

    def get_data(self) -> SummaryReportData:
        summary_item_locator = (
            "*[class$='modal-box__body'] div[class*='description-list'][data-ouia-component-id]"
        )
        all_data_points = {}
        # .all() resolves immediately, so let's first wait until something is visible
        self._driver.locator(summary_item_locator).first.wait_for()
        for summary_item in self._driver.locator(summary_item_locator).all():
            key = summary_item.get_attribute("data-ouia-component-id")
            if not key:
                continue
            label = str(summary_item.locator("dt").first.text_content())
            value = str(summary_item.locator("dd").first.text_content())
            parsing_fn = self.VALUE_TRANSFORMER_MAP.get(key, to_int)
            parsed_value = parsing_fn(value)
            data_point = SummaryReportDataPoint(
                key=key, label=label, value=value, parsed_value=parsed_value
            )
            all_data_points[key] = data_point
        report = SummaryReportData(all_data_points)
        return report


def _wait_for_scan(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        timeout_start = time.monotonic()
        while timeout > (time.monotonic() - timeout_start):
            if result := func(self, *args, **kwargs):
                return result
        raise FailedScanException("Scan did not succeed in specified time")

    return wrapper


class ScanListElem(AbstractListItem):
    @_wait_for_scan
    def download_scan(self) -> Download | None:
        try:
            with self._client.driver.expect_download() as download_info:
                self.select_action("download", timeout=10_000)
            download = download_info.value
            download.path()  # blocks the script while file is downloaded
            return download
        except PlaywrightTimeoutError:
            self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()

    @_wait_for_scan
    def download_scan_modal(
        self, sort_by: ScansModalTableColumns, ordering: ColumnOrdering, item: int
    ) -> Download | None:
        try:
            scans_modal = self._open_scans_modal()
            scans_modal.sort_table(sort_by, ordering)
            download = scans_modal.get_nth_download(item)
            scans_modal.cancel()
            return download
        except PlaywrightTimeoutError:
            scans_modal.cancel()
            self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()

    @_wait_for_scan
    def read_summary_modal(self) -> SummaryReportData | None:
        try:
            summary_modal = self._open_summary_modal()
            data = summary_modal.get_data()
            summary_modal.cancel()
            return data
        except PlaywrightTimeoutError:
            self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()

    def _open_scans_modal(self) -> ScanHistoryModal:
        last_scanned_locator = "td[data-label='Last scanned'] button"
        self.locator.locator(last_scanned_locator).click()
        return ScanHistoryModal(client=self._client)

    def _open_summary_modal(self) -> SummaryReportModal:
        self.select_action("summary")
        return SummaryReportModal(client=self._client)


class ScansMainPage(MainPageMixin):
    ITEM_CLASS = ScanListElem

    @creates_toast
    @service
    @record_action
    def download_scan(self, scan_name: str) -> ScansMainPage:
        scan: ScanListElem = self._get_item(scan_name)
        downloaded_report = scan.download_scan()
        self._client.downloaded_files.append(downloaded_report)
        return self

    @creates_toast
    @service
    @record_action
    def download_scan_modal(
        self, scan_name: str, sort_by: ScansModalTableColumns, ordering: ColumnOrdering, item: int
    ) -> ScansMainPage:
        scan: ScanListElem = self._get_item(scan_name)
        downloaded_report = scan.download_scan_modal(sort_by, ordering, item)
        self._client.downloaded_files.append(downloaded_report)
        return self

    @service
    @record_action
    def read_summary_modal(self, scan_name: str):
        scan: ScanListElem = self._get_item(scan_name)
        summary_data = scan.read_summary_modal()
        self._client.page_contents.append(summary_data)
        return self
