from __future__ import annotations

from playwright.sync_api import TimeoutError

from camayoc.ui.types import UIPage


class ToastNotifications(UIPage):
    def _dismiss_notifications(self, ensure_notifications_appeared=False):
        default_timeout = 100  # milliseconds!
        current_timeout = 5000 if ensure_notifications_appeared else default_timeout
        notifications_selector = ".pf-m-toast > li > .pf-c-alert"

        notifications = self._driver.locator(notifications_selector)
        while True:
            try:
                notifications.nth(0).locator("button[aria-label^=Close]").click(
                    timeout=current_timeout
                )
                current_timeout = default_timeout
            except TimeoutError:
                break
