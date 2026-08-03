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
    NAME_FIELD_LABEL = "Scan name"

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
