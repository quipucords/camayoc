from __future__ import annotations

from playwright.sync_api import Download

from ..components.items_list import AbstractListItem
from ..mixins import MainPageMixin
from camayoc.ui.decorators import creates_toast
from camayoc.ui.decorators import record_action
from camayoc.ui.decorators import service


class ScanListElem(AbstractListItem):
    def download_scan(self) -> Download:
        scan_locator = "div.list-view-pf-actions button[title=Download]"
        # timeout argument below is in milliseconds; this is how long
        # script will wait for download button to appear
        with self.locator.page.expect_download() as download_info:
            self.locator.locator(scan_locator).click(timeout=30_000)
        download = download_info.value
        download.path()  # blocks the script while file is downloaded
        return download


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
