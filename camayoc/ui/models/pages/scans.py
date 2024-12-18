from __future__ import annotations

import time

from playwright.sync_api import Download
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from camayoc.exceptions import FailedScanException
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


class ScanListElem(AbstractListItem):
    def download_scan(self) -> Download:
        timeout_start = time.monotonic()
        timeout = self._client._camayoc_config.camayoc.scan_timeout
        download_locator = (
            "button[data-ouia-component-id=action_menu_toggle] "
            "~ div *[data-ouia-component-id=download] button"
        )
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

    def _toggle_kebab(self) -> None:
        kebab_menu_locator = "button[data-ouia-component-id=action_menu_toggle]"
        self.locator.locator(kebab_menu_locator).click()

    def _open_scans_popup(self) -> ScanHistoryPopup:
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
