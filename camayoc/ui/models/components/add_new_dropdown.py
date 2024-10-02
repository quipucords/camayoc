from __future__ import annotations

from playwright.sync_api import TimeoutError

from camayoc.exceptions import MisconfiguredWidgetException
from camayoc.types.ui import UIPage


class AddNewDropdown(UIPage):
    def open_create_new_modal(self, type_ouiaid):
        default_timeout = 5000  # 5s
        add_button_locator = getattr(self, "ADD_BUTTON_LOCATOR")
        if not add_button_locator:
            msg = "{} requires class property 'ADD_BUTTON_LOCATOR' to be set [object={}]"
            raise MisconfiguredWidgetException(msg.format(type(self).__name__, self))

        dropdown_item_locator = (
            f"{add_button_locator} ~ div ul li[data-ouia-component-id={type_ouiaid}]"
        )

        exp_msg = (
            "Could not open modal using dropdown menu [button locator={} ;"
            "dropdown item locator={}]"
        ).format(add_button_locator, dropdown_item_locator)
        exp = TimeoutError(exp_msg)
        for _ in range(5):
            try:
                self._driver.locator(add_button_locator).click(timeout=default_timeout)
                self._driver.locator(dropdown_item_locator).click(timeout=default_timeout)
                return
            except TimeoutError as e:
                exp = e
                continue
        raise exp
