from __future__ import annotations

from playwright.sync_api import Download

from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service

from ..components.items_list import AbstractListItem
from ..mixins import MainPageMixin


class ReportListElem(AbstractListItem):
    def download_report(self) -> Download:
        with self._client.driver.expect_download() as download_info:
            self.select_action("download-report", timeout=10_000)
        download = download_info.value
        download.path()
        return download


class ReportsMainPage(MainPageMixin):
    ITEM_CLASS = ReportListElem
    ITEM_LABEL_LOCATOR = "td[data-label='Scan name']"

    def _search_for_item_by_name(self, name: str):
        filter_field_button_locator = (
            "div[class*=-c-toolbar__item] button[id]:has(span[class*=-c-menu-toggle])"
        )
        filter_field_values_locator = "body > div[class*=-c-menu]"

        filter_field_button = self._driver.locator(filter_field_button_locator).locator("nth=0")
        if filter_field_button.text_content() != "Scan name":
            filter_field_button.click()
            values_list = self._driver.locator(filter_field_values_locator)
            values_list.locator("text='Scan name'").click()
        self._driver.fill("input[placeholder$='scan name']", name)
        self._driver.keyboard.press("Enter")

    @creates_toast
    @service
    @record_action
    def download_report(self, scan_name: str) -> ReportsMainPage:
        report: ReportListElem = self._get_item(scan_name)
        downloaded_report = report.download_report()
        self._client.downloaded_files.append(downloaded_report)
        return self

    @service
    @record_action
    def assert_report_present(self, scan_name: str) -> ReportsMainPage:
        self._get_item(scan_name)
        return self
