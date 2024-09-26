from __future__ import annotations

import time

from playwright.sync_api import Download
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from camayoc.config import settings
from camayoc.exceptions import FailedScanException
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service
from camayoc.ui.enums import Pages

from ..components.items_list import AbstractListItem
from ..components.popup import PopUp
from ..mixins import MainPageMixin
from .abstract_page import AbstractPage


class ScanHistoryPopup(PopUp, AbstractPage):
    SAVE_LOCATOR = None
    CANCEL_LOCATOR = "*[class$='modal-box__close'] button"
    SAVE_RESULT_CLASS = None
    CANCEL_RESULT_CLASS = Pages.SCANS

    def get_last_download(self) -> Download:
        table_row_locator = "table[data-ouia-component-id=scan_jobs_table] tbody tr"
        download_button_locator = "td[data-label=Download] button"

        last_download = self._driver.locator(table_row_locator).last
        with self._driver.expect_download() as download_info:
            last_download.locator(download_button_locator).click(timeout=10_000)
        download = download_info.value
        download.path()  # blocks the script while file is downloaded
        return download


class ScanListElem(AbstractListItem):
    def download_scan(self) -> Download:
        if settings.camayoc.use_uiv2:
            return self._download_scan_v2()

        scan_locator = "td[class*=-c-table__action] button[data-ouia-component-id=download]"
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        while timeout > (time.monotonic() - timeout_start):
            try:
                with self.locator.page.expect_download() as download_info:
                    self.locator.locator(scan_locator).click(timeout=10_000)
                download = download_info.value
                download.path()  # blocks the script while file is downloaded
                return download
            except PlaywrightTimeoutError:
                self._client.driver.locator(
                    "div[class*=-c-toolbar] button[data-ouia-component-id=refresh]"
                ).click()
        raise FailedScanException("Scan could not be downloaded")

    def _download_scan_v2(self) -> Download:
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        while timeout > (time.monotonic() - timeout_start):
            try:
                scans_popup = self._open_scans()
                download = scans_popup.get_last_download()
                scans_popup.cancel()
                return download
            except PlaywrightTimeoutError:
                scans_popup.cancel()
                self._client.driver.locator(
                    "div[class*=-c-toolbar] button[data-ouia-component-id=refresh]"
                ).click()
        raise FailedScanException("Scan could not be downloaded")

    def _open_scans(self) -> ScanHistoryPopup:
        last_scanned_locator = "td[data-label='Last scanned'] button"
        self.locator.locator(last_scanned_locator).click()
        return ScanHistoryPopup(client=self._client)


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
