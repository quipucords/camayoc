from __future__ import annotations

import time
from datetime import datetime

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
from camayoc.ui.enums import ScansPopupTableColumns

from ..components.items_list import AbstractListItem
from ..components.popup import PopUp
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage

REFRESH_BUTTON_LOCATOR = "div[class*=-c-toolbar] button[data-ouia-component-id=refresh]"
KEBAB_ITEM_LOCATOR_TEMPLATE = (
    "button[data-ouia-component-id=action_menu_toggle] ~ div *[data-ouia-component-id={}] button"
)


class ScanHistoryPopup(PopUp, AbstractPage):
    SAVE_LOCATOR = None
    CANCEL_LOCATOR = "*[class$='modal-box__close'] button"
    SAVE_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = Pages.SCANS

    def sort_table(self, sort_by: ScansPopupTableColumns, ordering: ColumnOrdering) -> None:
        tries = 0
        table_header_locator = (
            "table[data-ouia-component-id=scan_jobs_table] thead "
            f"th[data-ouia-component-id={sort_by.value}]"
        )
        while 3 >= tries:
            header = self._driver.locator(table_header_locator)
            if header.get_attribute("aria-sort") == ordering.value:
                return
            header.click()
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


class SummaryReportPopup(PopUp, AbstractPage):
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


class ScanListElem(AbstractListItem):
    def download_scan(self) -> Download:
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        download_locator = KEBAB_ITEM_LOCATOR_TEMPLATE.format("download")
        while timeout > (time.monotonic() - timeout_start):
            try:
                self._toggle_kebab()
                with self._client.driver.expect_download() as download_info:
                    self.locator.locator(download_locator).click(timeout=10_000)
                download = download_info.value
                download.path()  # blocks the script while file is downloaded
                self._toggle_kebab()
                return download
            except PlaywrightTimeoutError:
                self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()
        raise FailedScanException("Scan could not be downloaded")

    def download_scan_modal(
        self, sort_by: ScansPopupTableColumns, ordering: ColumnOrdering, item: int
    ) -> Download:
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        while timeout > (time.monotonic() - timeout_start):
            try:
                scans_popup = self._open_scans_popup()
                scans_popup.sort_table(sort_by, ordering)
                download = scans_popup.get_nth_download(item)
                scans_popup.cancel()
                return download
            except PlaywrightTimeoutError:
                scans_popup.cancel()
                self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()
        raise FailedScanException("Scan could not be downloaded")

    def read_summary_modal(self) -> SummaryReportData:
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        while timeout > (time.monotonic() - timeout_start):
            try:
                summary_popup = self._open_summary_popup()
                data = summary_popup.get_data()
                summary_popup.cancel()
                return data
            except PlaywrightTimeoutError:
                self._client.driver.locator(REFRESH_BUTTON_LOCATOR).click()
        raise FailedScanException("summary report could not be downloaded")

    def _toggle_kebab(self) -> None:
        kebab_menu_locator = "button[data-ouia-component-id=action_menu_toggle]"
        self.locator.locator(kebab_menu_locator).click()

    def _open_scans_popup(self) -> ScanHistoryPopup:
        last_scanned_locator = "td[data-label='Last scanned'] button"
        self.locator.locator(last_scanned_locator).click()
        return ScanHistoryPopup(client=self._client)

    def _open_summary_popup(self) -> SummaryReportPopup:
        summary_locator = KEBAB_ITEM_LOCATOR_TEMPLATE.format("summary")
        self._toggle_kebab()
        self.locator.locator(summary_locator).click()
        return SummaryReportPopup(client=self._client)


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
        self, scan_name: str, sort_by: ScansPopupTableColumns, ordering: ColumnOrdering, item: int
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
